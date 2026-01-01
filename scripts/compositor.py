"""
Overlay compositing for Snapchat memories (images and videos).
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from metadata import copy_metadata_with_exiftool
from error_logger import ErrorLogger


def extract_sid_from_filename(file_path: Path) -> str:
    """Extract session ID from filename.

    Args:
        file_path: Path object with filename format: YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext

    Returns:
        Session ID (last underscore-separated part before extension) or 'unknown'
    """
    return file_path.stem.split('_')[-1] if '_' in file_path.stem else 'unknown'


def find_overlay_pairs(output_dir: Path, pairs_cache_file: str = "overlay_pairs.json", use_cache: bool = True) -> List[Dict]:
    """Find all base media files with matching overlay files.

    Args:
        output_dir: Base output directory containing images/videos/overlays
        pairs_cache_file: Path to cache file
        use_cache: If True, load from cache if it exists

    Returns:
        List of dicts with:
        - base_file: Path to base image/video
        - overlay_file: Path to overlay PNG
        - media_type: 'image' or 'video'
        - sid: Session ID
    """
    # Scan overlay directory first to get stats for cache validation
    overlay_dir = output_dir / "overlays"
    if not overlay_dir.exists():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Overlays directory not found: {overlay_dir}")
        return []

    # Get directory stats for cache validation
    try:
        overlay_stats = overlay_dir.stat()
        current_mtime = overlay_stats.st_mtime
        # Fast way to get file count
        current_count = len(list(overlay_dir.glob("*_overlay.png")))
    except Exception:
        current_mtime = 0
        current_count = 0

    # Try to load from cache
    if use_cache and os.path.exists(pairs_cache_file):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking overlay cache...")
        try:
            with open(pairs_cache_file, 'r') as f:
                cached_data = json.load(f)

            # Check if cache is stale
            cache_mtime = cached_data.get('overlay_dir_mtime', 0)
            cache_count = cached_data.get('overlay_dir_count', 0)
            
            is_stale = False
            if current_count != cache_count:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache invalid: Overlay file count changed ({cache_count} -> {current_count})")
                is_stale = True
            elif abs(current_mtime - cache_mtime) > 1.0: # 1 second tolerance
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache invalid: Overlays directory modified since last run")
                is_stale = True
            
            if not is_stale and cached_data.get('count', 0) > 0:
                # Cache is valid
                pairs = []
                for item in cached_data['pairs']:
                    pairs.append({
                        'base_file': Path(item['base_file']),
                        'overlay_file': Path(item['overlay_file']),
                        'media_type': item['media_type'],
                        'sid': item['sid']
                    })

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache valid ({len(pairs)} pairs)")
                return pairs
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache check failed: {e}, rebuilding...")

    # Build pairs from filesystem
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning filesystem for overlay pairs...")
    pairs = []

    # Get overlay files (we already counted them, but need the specific paths now)
    overlay_files = list(overlay_dir.glob("*_overlay.png"))
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(overlay_files)} overlay files")

    if len(overlay_files) == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No overlay files found in {overlay_dir}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] This means either:")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   1. Your memories don't have overlays (Snapchat didn't provide any)")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   2. Overlays weren't downloaded (check download_progress.json)")
        return pairs

    corrupt_overlays = []
    skipped_no_base = []

    for overlay_file in overlay_files:
        # Validate overlay file before processing
        try:
            file_size = overlay_file.stat().st_size

            # Check for zero-byte files
            if file_size == 0:
                corrupt_overlays.append({
                    'file': overlay_file.name,
                    'reason': 'Zero-byte file (corrupt download from Snapchat)'
                })
                continue

            # Check file is readable
            if not os.access(overlay_file, os.R_OK):
                corrupt_overlays.append({
                    'file': overlay_file.name,
                    'reason': 'File not readable (permission denied)'
                })
                continue

        except Exception as e:
            corrupt_overlays.append({
                'file': overlay_file.name,
                'reason': f'Cannot access file: {str(e)}'
            })
            continue

        # Parse filename: YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX_overlay.png
        filename = overlay_file.stem  # Remove .png

        # Remove _overlay suffix
        if not filename.endswith("_overlay"):
            continue

        base_filename = filename[:-8]  # Remove "_overlay"

        # Extract SID from filename (last part before _overlay)
        parts = base_filename.split('_')
        if len(parts) < 4:
            continue

        sid = parts[-1]  # Last part is the SID (e.g., "036cb75f")

        # Determine media type from filename
        if "_Image_" in base_filename:
            media_type = "image"
            base_dir = output_dir / "images"
        elif "_Video_" in base_filename:
            media_type = "video"
            base_dir = output_dir / "videos"
        else:
            continue

        # Find matching base file by SID (timezone-agnostic)
        # Match pattern: *_sidXXXXXXXX.ext (where SID is the last part before extension)
        base_files = list(base_dir.glob(f"*_{sid}.*"))

        if base_files:
            pairs.append({
                'base_file': base_files[0],
                'overlay_file': overlay_file,
                'media_type': media_type,
                'sid': sid
            })
        else:
            skipped_no_base.append({
                'overlay': overlay_file.name,
                'sid': sid,
                'media_type': media_type
            })

    # Report corrupt overlays if found
    if corrupt_overlays:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Found {len(corrupt_overlays)} corrupt overlay file(s)!")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] These files will be skipped:")
        for item in corrupt_overlays[:10]:  # Show first 10
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   - {item['file']}: {item['reason']}")
        if len(corrupt_overlays) > 10:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ... and {len(corrupt_overlays) - 10} more")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Suggestion: Re-download your Snapchat data export to get valid overlay files")

    # Report overlays without matching base files
    if skipped_no_base:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Found {len(skipped_no_base)} overlay(s) without matching base files")
        if len(skipped_no_base) <= 5:
            for item in skipped_no_base:
                print(f"[{datetime.now().strftime('%H:%M:%S')}]   - {item['overlay']} (SID: {item['sid']}, type: {item['media_type']})")

    # Save to cache
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(pairs)} valid pairs, saving to cache...")

    # Provide diagnostic info if no pairs found
    if len(pairs) == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: No matching base files found for any overlays!")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked directories:")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   - Images: {output_dir / 'images'}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   - Videos: {output_dir / 'videos'}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Possible causes:")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   1. Base files have different SIDs than overlay files")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   2. Base files are in a different location")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   3. Files were renamed manually after download")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   4. All overlay files are corrupt (see warnings above)")

    cache_data = {
        'created': datetime.now().isoformat(),
        'count': len(pairs),
        'overlay_dir_mtime': current_mtime,
        'overlay_dir_count': current_count,
        'pairs': [
            {
                'base_file': str(p['base_file']),
                'overlay_file': str(p['overlay_file']),
                'media_type': p['media_type'],
                'sid': p['sid']
            }
            for p in pairs
        ]
    }

    try:
        with open(pairs_cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache saved to {pairs_cache_file}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Could not save cache: {e}")

    return pairs


def composite_image(base_file: Path, overlay_file: Path, output_dir: Path, has_exiftool: bool = False, error_logger: Optional[ErrorLogger] = None) -> Tuple[bool, str]:
    """Composite overlay onto image using Pillow.

    Args:
        base_file: Path to base image
        overlay_file: Path to overlay PNG
        output_dir: Output directory for composited images
        has_exiftool: Whether exiftool is available (auto-copies metadata if True)
        error_logger: Optional error logger for detailed error tracking

    Returns:
        (success, message)
    """
    try:
        from PIL import Image

        # Validate base file (overlay validation already done in find_overlay_pairs())
        base_size = base_file.stat().st_size
        if base_size == 0:
            error_msg = "Base image file is empty (0 bytes)"
            if error_logger:
                sid = extract_sid_from_filename(base_file)
                error_logger.log_composite_error(
                    sid=sid,
                    media_type='image',
                    base_file=str(base_file),
                    overlay_file=str(overlay_file),
                    error_message=error_msg,
                    additional_context={'base_file_size': 0}
                )
            return False, error_msg

        # Open base image and overlay
        base = Image.open(base_file)
        overlay = Image.open(overlay_file)

        # Convert to RGBA if needed
        if base.mode != 'RGBA':
            base = base.convert('RGBA')
        if overlay.mode != 'RGBA':
            overlay = overlay.convert('RGBA')

        # Resize overlay to match base if needed
        if overlay.size != base.size:
            overlay = overlay.resize(base.size, Image.Resampling.BILINEAR)

        # Composite overlay onto base
        composited = Image.alpha_composite(base, overlay)

        # Convert back to RGB for JPEG
        if composited.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', composited.size, (255, 255, 255))
            background.paste(composited, mask=composited.split()[3])  # Use alpha channel as mask
            composited = background

        # Create output filename
        output_filename = base_file.stem + "_composited" + base_file.suffix
        output_path = output_dir / "composited" / "images" / output_filename

        # Save with high quality
        if base_file.suffix.lower() in ['.jpg', '.jpeg']:
            composited.save(output_path, 'JPEG', quality=95, optimize=True)
        else:
            composited.save(output_path, quality=95, optimize=True)

        # Set file timestamps to match original
        stat = os.stat(base_file)
        os.utime(output_path, (stat.st_atime, stat.st_mtime))

        # Copy metadata using exiftool if available
        if has_exiftool:
            copy_metadata_with_exiftool(base_file, output_path, has_exiftool)

        return True, "Success"

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        if error_logger:
            sid = extract_sid_from_filename(base_file)
            error_logger.log_composite_error(
                sid=sid,
                media_type='image',
                base_file=str(base_file),
                overlay_file=str(overlay_file),
                error_message=error_msg,
                exception=e,
                additional_context={
                    'base_file_size': base_file.stat().st_size if base_file.exists() else 0,
                    'overlay_file_size': overlay_file.stat().st_size if overlay_file.exists() else 0
                }
            )
        return False, error_msg


def get_video_dimensions(video_file: Path) -> Tuple[int, int]:
    """Get video dimensions accounting for rotation metadata.

    Args:
        video_file: Path to video file

    Returns:
        (width, height) tuple accounting for rotation
    """
    try:
        # Get video stream info including rotation
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height:stream_side_data=rotation',
            '-of', 'json',
            str(video_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            # Fallback to simple dimension query
            return _get_simple_dimensions(video_file)

        import json
        data = json.loads(result.stdout)
        stream = data.get('streams', [{}])[0]

        width = stream.get('width', 0)
        height = stream.get('height', 0)

        # Check for rotation in side_data
        rotation = 0
        side_data = stream.get('side_data_list', [])
        for sd in side_data:
            if 'rotation' in sd:
                rotation = abs(int(sd['rotation']))
                break

        # Swap dimensions if rotated 90 or 270 degrees
        if rotation in [90, 270]:
            width, height = height, width

        return width, height

    except Exception:
        return _get_simple_dimensions(video_file)


def _get_simple_dimensions(video_file: Path) -> Tuple[int, int]:
    """Fallback method to get video dimensions without rotation handling.

    Args:
        video_file: Path to video file

    Returns:
        (width, height) tuple
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            str(video_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dims = result.stdout.strip().split('x')
            if len(dims) == 2:
                return int(dims[0]), int(dims[1])
    except Exception:
        pass

    return 1920, 1080  # Default fallback


def composite_video(base_file: Path, overlay_file: Path, output_dir: Path, has_exiftool: bool = False, error_logger: Optional[ErrorLogger] = None) -> Tuple[bool, str]:
    """Composite overlay onto video using FFmpeg.

    Args:
        base_file: Path to base video
        overlay_file: Path to overlay PNG
        output_dir: Output directory for composited videos
        has_exiftool: Whether exiftool is available
        error_logger: Optional error logger for detailed error tracking

    Returns:
        (success, message)
    """
    try:
        # Validate base file (overlay validation already done in find_overlay_pairs())
        base_size = base_file.stat().st_size
        if base_size == 0:
            error_msg = "Base video file is empty (0 bytes)"
            if error_logger:
                sid = extract_sid_from_filename(base_file)
                error_logger.log_composite_error(
                    sid=sid,
                    media_type='video',
                    base_file=str(base_file),
                    overlay_file=str(overlay_file),
                    error_message=error_msg,
                    additional_context={'base_file_size': 0}
                )
            return False, error_msg

        # Create output filename
        output_filename = base_file.stem + "_composited" + base_file.suffix
        output_path = output_dir / "composited" / "videos" / output_filename

        # Get video dimensions (accounting for rotation)
        video_width, video_height = get_video_dimensions(base_file)

        # Build FFmpeg command with proper overlay scaling
        # Scale overlay to match video, then composite it
        filter_complex = f"[1:v]scale={video_width}:{video_height}[ovr];[0:v][ovr]overlay=0:0:format=auto"

        cmd = [
            'ffmpeg',
            '-i', str(base_file),           # Input video
            '-i', str(overlay_file),        # Input overlay
            '-filter_complex', filter_complex,  # Scale and overlay
            '-codec:a', 'copy',             # Copy audio without re-encoding
            '-y',                           # Overwrite output file
            str(output_path)
        ]

        # Run FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max per video
        )

        if result.returncode != 0:
            error_msg = f"FFmpeg error: {result.stderr[:500]}"  # Increased from 100 to 500 chars
            if error_logger:
                sid = extract_sid_from_filename(base_file)
                error_logger.log_composite_error(
                    sid=sid,
                    media_type='video',
                    base_file=str(base_file),
                    overlay_file=str(overlay_file),
                    error_message=error_msg,
                    command=' '.join(cmd),
                    additional_context={
                        'ffmpeg_returncode': result.returncode,
                        'ffmpeg_stderr': result.stderr,
                        'video_dimensions': f"{video_width}x{video_height}"
                    }
                )
            return False, error_msg

        # Set file timestamps to match original
        stat = os.stat(base_file)
        os.utime(output_path, (stat.st_atime, stat.st_mtime))

        # Copy metadata using exiftool if available
        if has_exiftool:
            copy_metadata_with_exiftool(base_file, output_path, has_exiftool)

        return True, "Success"

    except subprocess.TimeoutExpired as e:
        error_msg = "Timeout (video too long - exceeded 5 minutes)"
        if error_logger:
            sid = extract_sid_from_filename(base_file)
            error_logger.log_composite_error(
                sid=sid,
                media_type='video',
                base_file=str(base_file),
                overlay_file=str(overlay_file),
                error_message=error_msg,
                exception=e,
                additional_context={'timeout_seconds': 300}
            )
        return False, error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        if error_logger:
            sid = extract_sid_from_filename(base_file)
            error_logger.log_composite_error(
                sid=sid,
                media_type='video',
                base_file=str(base_file),
                overlay_file=str(overlay_file),
                error_message=error_msg,
                exception=e,
                additional_context={
                    'base_file_size': base_file.stat().st_size if base_file.exists() else 0,
                    'overlay_file_size': overlay_file.stat().st_size if overlay_file.exists() else 0
                }
            )
        return False, error_msg
