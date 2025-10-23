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
    # Try to load from cache
    if use_cache and os.path.exists(pairs_cache_file):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading overlay pairs from cache...")
        try:
            with open(pairs_cache_file, 'r') as f:
                cached_data = json.load(f)

            # Convert string paths back to Path objects
            pairs = []
            for item in cached_data['pairs']:
                pairs.append({
                    'base_file': Path(item['base_file']),
                    'overlay_file': Path(item['overlay_file']),
                    'media_type': item['media_type'],
                    'sid': item['sid']
                })

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded {len(pairs)} pairs from cache (created {cached_data['created']})")
            return pairs
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache load failed: {e}, rebuilding...")

    # Build pairs from filesystem
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning filesystem for overlay pairs...")
    pairs = []

    # Scan overlay directory
    overlay_dir = output_dir / "overlays"
    if not overlay_dir.exists():
        return pairs

    for overlay_file in overlay_dir.glob("*_overlay.png"):
        # Parse filename: YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX_overlay.png
        filename = overlay_file.stem  # Remove .png

        # Remove _overlay suffix
        if filename.endswith("_overlay"):
            base_filename = filename[:-8]  # Remove "_overlay"
        else:
            continue

        # Determine media type from filename
        if "_Image_" in base_filename:
            media_type = "image"
            base_dir = output_dir / "images"
        elif "_Video_" in base_filename:
            media_type = "video"
            base_dir = output_dir / "videos"
        else:
            continue

        # Find matching base file (could be .jpg, .mp4, etc.)
        base_files = list(base_dir.glob(f"{base_filename}.*"))
        if base_files:
            # Extract SID from filename (last part before extension)
            parts = base_filename.split('_')
            sid = parts[-1] if len(parts) >= 4 else ""

            pairs.append({
                'base_file': base_files[0],
                'overlay_file': overlay_file,
                'media_type': media_type,
                'sid': sid
            })

    # Save to cache
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(pairs)} pairs, saving to cache...")
    cache_data = {
        'created': datetime.now().isoformat(),
        'count': len(pairs),
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


def composite_image(base_file: Path, overlay_file: Path, output_dir: Path, has_exiftool: bool = False) -> Tuple[bool, str]:
    """Composite overlay onto image using Pillow.

    Args:
        base_file: Path to base image
        overlay_file: Path to overlay PNG
        output_dir: Output directory for composited images
        has_exiftool: Whether exiftool is available (auto-copies metadata if True)

    Returns:
        (success, message)
    """
    try:
        from PIL import Image

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
        return False, f"Error: {str(e)}"


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


def composite_video(base_file: Path, overlay_file: Path, output_dir: Path, has_exiftool: bool = False) -> Tuple[bool, str]:
    """Composite overlay onto video using FFmpeg.

    Args:
        base_file: Path to base video
        overlay_file: Path to overlay PNG
        output_dir: Output directory for composited videos
        has_exiftool: Whether exiftool is available

    Returns:
        (success, message)
    """
    try:
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
            return False, f"FFmpeg error: {result.stderr[:100]}"

        # Set file timestamps to match original
        stat = os.stat(base_file)
        os.utime(output_path, (stat.st_atime, stat.st_mtime))

        # Copy metadata using exiftool if available
        if has_exiftool:
            copy_metadata_with_exiftool(base_file, output_path, has_exiftool)

        return True, "Success"

    except subprocess.TimeoutExpired:
        return False, "Timeout (video too long)"
    except Exception as e:
        return False, f"Error: {str(e)}"
