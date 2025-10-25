"""
Download and organize Snapchat memories.
"""

import os
import time
import zipfile
import shutil
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List

from snap_config import check_exiftool, check_pywin32, check_pillow, check_ffmpeg, check_timezone_lookup
from snap_parser import parse_html_file
from progress import ProgressTracker
from metadata import (
    set_file_timestamps,
    add_gps_metadata,
    update_existing_file_metadata,
    parse_location,
    get_timezone_from_coordinates,
    HAS_TIMEZONE_LOOKUP
)
from compositor import find_overlay_pairs, composite_image, composite_video
from timezone_converter import (
    utc_to_local,
    utc_to_timezone,
    generate_local_filename,
    parse_filename_for_sid,
    convert_file_timestamps_to_local
)


class SnapchatDownloader:
    """Download and organize Snapchat memories.

    This is the main orchestrator class that coordinates:
    - HTML parsing
    - File downloads
    - Progress tracking
    - Metadata operations
    - Overlay compositing
    """

    def __init__(self, html_file: str, output_dir: str = "memories"):
        """Initialize the downloader with configuration.

        Args:
            html_file: Path to memories_history.html
            output_dir: Output directory for downloaded memories
        """
        self.html_file = html_file
        self.output_dir = Path(output_dir)
        self.progress_tracker = ProgressTracker()
        self.session = requests.Session()

        # Check for optional dependencies
        self.has_exiftool = check_exiftool()
        self.has_pywin32 = check_pywin32()
        has_pillow, _ = check_pillow()
        self.has_pillow = has_pillow
        self.has_ffmpeg = check_ffmpeg()

        # Create output directories
        self._create_output_dirs()

    def _create_output_dirs(self):
        """Create all necessary output directories."""
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "overlays").mkdir(exist_ok=True)
        (self.output_dir / "composited").mkdir(exist_ok=True)
        (self.output_dir / "composited" / "images").mkdir(exist_ok=True)
        (self.output_dir / "composited" / "videos").mkdir(exist_ok=True)

    def download_all(self, delay: float = 2.0):
        """Download all memories with progress tracking.

        Args:
            delay: Delay between downloads in seconds
        """
        # Parse HTML to get list of memories
        memories = parse_html_file(self.html_file)

        # Calculate what needs to be downloaded
        total = len(memories)
        already_downloaded = len([m for m in memories if self.progress_tracker.is_downloaded(m['sid'])])
        to_download = total - already_downloaded

        print(f"\nTotal memories: {total}")
        print(f"Already downloaded: {already_downloaded}")
        print(f"To download: {to_download}\n")

        if to_download == 0:
            print("All memories already downloaded!")
            return

        # Download each memory
        downloaded_count = 0
        failed_count = 0
        skipped_count = 0

        for i, memory in enumerate(memories, 1):
            sid = memory['sid']

            if self.progress_tracker.is_downloaded(sid):
                print(f"[{i}/{total}] Skipping {sid[:8]}... (already downloaded)")
                skipped_count += 1
                continue

            print(f"[{i}/{total}] Downloading {memory['date']} - {memory['media_type']}...", end=" ")

            success, message = self._download_memory(memory, delay)
            print(message)

            if success:
                downloaded_count += 1
            else:
                failed_count += 1

            # Rate limiting
            if i < total:
                time.sleep(delay)

        # Print summary
        self._print_download_summary(downloaded_count, failed_count, skipped_count, total)

    def _download_memory(self, memory: Dict, retry_delay: float = 5.0) -> Tuple[bool, str]:
        """Download a single memory with retry logic.

        Args:
            memory: Memory dictionary from HTML parser
            retry_delay: Base delay for exponential backoff

        Returns:
            (success, message)
        """
        sid = memory['sid']

        # Check if already downloaded
        if self.progress_tracker.is_downloaded(sid):
            update_existing_file_metadata(
                self.output_dir, memory, sid,
                self.has_exiftool, self.has_pywin32
            )
            return True, "Already downloaded"

        # Check if previously failed too many times
        fail_count = self.progress_tracker.get_failure_count(sid)
        if fail_count >= 5:
            return False, f"Skipped (failed {fail_count} times)"

        # Retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self._attempt_download(memory, sid)
            except ValueError as e:
                error_msg = str(e)
                # Check if it's a rate limit error
                if '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"    Rate limited. Waiting {wait_time:.0f}s before retry...")
                        time.sleep(wait_time)
                        continue
                # Re-raise if not rate limit or final attempt
                raise

        # If all retries failed
        self.progress_tracker.record_failure(sid, memory, "Max retries exceeded")
        return False, "Error: Max retries exceeded"

    def _attempt_download(self, memory: Dict, sid: str) -> Tuple[bool, str]:
        """Single download attempt.

        Args:
            memory: Memory dictionary
            sid: Session ID

        Returns:
            (success, message)
        """
        try:
            # Download the file
            response = self.session.get(memory['download_url'], timeout=60)

            # Check for rate limiting
            if response.status_code == 429:
                raise ValueError(f"HTTP 429 Too Many Requests - Rate limited by server")

            response.raise_for_status()

            # Check if we got an HTML error page
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                raise ValueError(f"Received HTML error page instead of media (likely rate limited or error)")

            # Save to temporary file
            temp_file = self.output_dir / f"temp_{sid}.download"
            with open(temp_file, 'wb') as f:
                f.write(response.content)

            # Process the downloaded file
            if zipfile.is_zipfile(temp_file):
                temp_file.rename(self.output_dir / f"temp_{sid}.zip")
                temp_zip = self.output_dir / f"temp_{sid}.zip"
                self._extract_and_save_zip(temp_zip, memory, sid)
                temp_zip.unlink()
            else:
                media_type = self._detect_media_type(temp_file, content_type)
                if media_type:
                    self._save_direct_media(temp_file, memory, sid, media_type)
                    temp_file.unlink()
                else:
                    bad_file = self.output_dir / f"bad_{sid}.dat"
                    temp_file.rename(bad_file)
                    raise ValueError(f"Downloaded file is not a ZIP or recognized media. Saved to {bad_file}")

            # Mark as downloaded
            self.progress_tracker.mark_downloaded(sid, memory)
            return True, "Downloaded successfully"

        except Exception as e:
            self.progress_tracker.record_failure(sid, memory, str(e), e)
            # Clean up temp files
            for temp_name in [f"temp_{sid}.zip", f"temp_{sid}.download"]:
                temp_path = self.output_dir / temp_name
                if temp_path.exists():
                    temp_path.unlink()
            return False, f"Error: {str(e)}"

    def _detect_media_type(self, file_path: Path, content_type: str) -> str:
        """Detect if file is a video or image.

        Args:
            file_path: Path to file
            content_type: HTTP content-type header

        Returns:
            'video', 'image', or None
        """
        # Check content-type header first
        if 'video' in content_type:
            return 'video'
        elif 'image' in content_type:
            return 'image'

        # Check magic bytes
        with open(file_path, 'rb') as f:
            header = f.read(12)

        # Video signatures
        if header[4:8] == b'ftyp':  # MP4/MOV
            return 'video'
        elif header[:4] == b'RIFF' and header[8:12] == b'AVI ':
            return 'video'
        elif header[:3] == b'\x1a\x45\xdf':  # WebM/MKV
            return 'video'
        # Image signatures
        elif header[:2] == b'\xff\xd8':  # JPEG
            return 'image'
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image'
        elif header[:2] in (b'II', b'MM'):  # TIFF
            return 'image'
        elif header[:6] in (b'GIF87a', b'GIF89a'):
            return 'image'

        return None

    def _extract_and_save_zip(self, temp_zip: Path, memory: Dict, sid: str):
        """Extract and save files from ZIP archive.

        Args:
            temp_zip: Path to temporary ZIP file
            memory: Memory dictionary
            sid: Session ID
        """
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                filename = file_info.filename
                is_overlay = 'overlay' in filename
                ext = filename.split('.')[-1]

                # Determine output directory
                if is_overlay:
                    output_subdir = self.output_dir / "overlays"
                elif memory['media_type'].lower() == 'image':
                    output_subdir = self.output_dir / "images"
                else:
                    output_subdir = self.output_dir / "videos"

                # Create new filename
                new_filename = self._format_filename(memory, ext, is_overlay)
                output_path = output_subdir / new_filename

                # Extract
                with zip_ref.open(file_info) as source, open(output_path, 'wb') as target:
                    target.write(source.read())

                # Set timestamps and GPS
                set_file_timestamps(output_path, memory, self.has_pywin32)
                add_gps_metadata(output_path, memory, self.has_exiftool)

    def _save_direct_media(self, temp_file: Path, memory: Dict, sid: str, media_type: str):
        """Save a direct media file (not in ZIP).

        Args:
            temp_file: Path to temporary file
            memory: Memory dictionary
            sid: Session ID
            media_type: 'video' or 'image'
        """
        # Determine extension
        with open(temp_file, 'rb') as f:
            header = f.read(12)

        if header[4:8] == b'ftyp':
            ext = 'mp4'
        elif header[:2] == b'\xff\xd8':
            ext = 'jpg'
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            ext = 'png'
        else:
            ext = 'mp4' if media_type == 'video' else 'jpg'

        # Determine output directory
        output_subdir = self.output_dir / ("videos" if media_type == 'video' else "images")

        # Create filename and copy
        new_filename = self._format_filename(memory, ext, is_overlay=False)
        output_path = output_subdir / new_filename
        shutil.copy2(temp_file, output_path)

        # Set timestamps and GPS
        set_file_timestamps(output_path, memory, self.has_pywin32)
        add_gps_metadata(output_path, memory, self.has_exiftool)

    def _format_filename(self, memory: Dict, extension: str, is_overlay: bool = False) -> str:
        """Create a filename from memory metadata.

        Args:
            memory: Memory dictionary
            extension: File extension
            is_overlay: Whether this is an overlay file

        Returns:
            Formatted filename
        """
        date_str = memory['date'].replace(' UTC', '')
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        date_part = dt.strftime('%Y-%m-%d')
        time_part = dt.strftime('%H%M%S')
        media_type = memory['media_type'].capitalize()
        sid_short = memory['sid'][:8]

        if is_overlay:
            return f"{date_part}_{time_part}_{media_type}_{sid_short}_overlay.png"
        else:
            return f"{date_part}_{time_part}_{media_type}_{sid_short}.{extension}"

    def _print_download_summary(self, downloaded: int, failed: int, skipped: int, total: int):
        """Print download summary statistics.

        Args:
            downloaded: Number of files downloaded
            failed: Number of failed downloads
            skipped: Number of skipped files
            total: Total number of files
        """
        print(f"\n{'='*60}")
        print(f"Download complete!")
        print(f"Downloaded: {downloaded}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Total: {total}")
        print(f"{'='*60}\n")

        if failed > 0:
            print(f"Failed downloads are tracked in {self.progress_tracker.progress_file}")
            print("Run the script again to retry failed downloads.\n")

        if not self.has_exiftool or not self.has_pywin32:
            print("TIP: To add missing features to your downloaded files:")
            if not self.has_exiftool:
                print("  - Install ExifTool to add GPS metadata")
            if not self.has_pywin32:
                print("  - Install pywin32 to set file creation dates")
            print("  Then run the script again to update existing files")
            print()

    def verify_downloads(self) -> Dict:
        """Verify all downloads are complete.

        Returns:
            Dictionary with verification results
        """
        memories = parse_html_file(self.html_file)
        return self.progress_tracker.verify_downloads(memories)

    def composite_all_overlays(self, images_only: bool = False, videos_only: bool = False,
                                rebuild_cache: bool = False):
        """Composite all overlays onto their base media files.

        Args:
            images_only: Only process images
            videos_only: Only process videos
            rebuild_cache: Force rebuild of overlay pairs cache
        """
        # Find all pairs
        pairs = find_overlay_pairs(self.output_dir, use_cache=not rebuild_cache)

        if not pairs:
            print("No overlay pairs found!")
            return

        # Filter by type
        if images_only:
            pairs = [p for p in pairs if p['media_type'] == 'image']
        elif videos_only:
            pairs = [p for p in pairs if p['media_type'] == 'video']

        # Separate by type
        image_pairs = [p for p in pairs if p['media_type'] == 'image']
        video_pairs = [p for p in pairs if p['media_type'] == 'video']

        print(f"\nFound {len(image_pairs)} images and {len(video_pairs)} videos with overlays")

        # Composite images
        if image_pairs:
            self._composite_images(image_pairs)

        # Composite videos
        if video_pairs:
            self._composite_videos(video_pairs)

    def _composite_images(self, pairs: List[Dict]):
        """Composite all image overlays.

        Args:
            pairs: List of image pairs
        """
        if not self.has_pillow:
            print("\nSkipping images - Pillow not installed")
            print("Install with: pip install Pillow")
            return

        # Filter out already composited
        pending_pairs = [
            p for p in pairs
            if not self.progress_tracker.is_composited(p['sid'], 'image')
        ]
        already_done = len(pairs) - len(pending_pairs)

        if already_done > 0:
            print(f"\nSkipping {already_done} already composited images")

        if not pending_pairs:
            print(f"\nAll {len(pairs)} images already composited!")
            return

        start_time = time.time()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Compositing {len(pending_pairs)} images...")

        if self.has_exiftool:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Metadata copying enabled (ExifTool detected, adds ~1.5s per image)")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Metadata copying disabled (ExifTool not found)")

        success_count = 0
        failed_count = 0

        for i, pair in enumerate(pending_pairs, 1):
            sid = pair['sid']
            filename = pair['base_file'].name

            success, message = composite_image(
                pair['base_file'],
                pair['overlay_file'],
                self.output_dir,
                has_exiftool=self.has_exiftool
            )

            if success:
                self.progress_tracker.mark_composited(
                    sid, 'image',
                    str(pair['base_file']),
                    str(pair['overlay_file'])
                )
                success_count += 1
                status = "OK"
            else:
                self.progress_tracker.record_composite_failure(
                    sid, 'image',
                    str(pair['base_file']),
                    str(pair['overlay_file']),
                    message
                )
                failed_count += 1
                status = "FAIL"

            # Progress stats
            percent = (i / len(pending_pairs)) * 100
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(pending_pairs) - i) / rate if rate > 0 else 0

            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] [{i}/{len(pending_pairs)} {percent:.1f}%] {status} {filename[:40]} | "
                  f"{rate:.1f} img/s | ETA: {eta:.0f}s", flush=True)

            # Save progress periodically
            if i % 10 == 0:
                self.progress_tracker.save_progress()

        # Final save
        self.progress_tracker.save_progress()

        total_time = time.time() - start_time
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Completed in {total_time:.1f}s ({total_time/len(pending_pairs):.2f}s per image)")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Images: {success_count} composited, {failed_count} failed, {already_done} skipped")

    def _composite_videos(self, pairs: List[Dict]):
        """Composite all video overlays.

        Args:
            pairs: List of video pairs
        """
        if not self.has_ffmpeg:
            print("\nSkipping videos - FFmpeg not installed")
            print("Install FFmpeg: https://ffmpeg.org/download.html")
            return

        print(f"\nCompositing {len(pairs)} videos...")
        success_count = 0

        for i, pair in enumerate(pairs, 1):
            sid = pair['sid']
            if self.progress_tracker.is_composited(sid, 'video'):
                print(f"[{i}/{len(pairs)}] Skipping {pair['base_file'].name} (already composited)")
                success_count += 1
                continue

            print(f"[{i}/{len(pairs)}] Compositing {pair['base_file'].name}...", end=" ")
            success, message = composite_video(
                pair['base_file'],
                pair['overlay_file'],
                self.output_dir,
                has_exiftool=self.has_exiftool
            )
            print(message)

            if success:
                self.progress_tracker.mark_composited(
                    sid, 'video',
                    str(pair['base_file']),
                    str(pair['overlay_file'])
                )
                success_count += 1
            else:
                self.progress_tracker.record_composite_failure(
                    sid, 'video',
                    str(pair['base_file']),
                    str(pair['overlay_file']),
                    message
                )

            self.progress_tracker.save_progress()

        failed_count = len(pairs) - success_count
        print(f"\nVideos: {success_count} composited, {failed_count} failed")

    def verify_composites(self) -> Dict:
        """Verify which files have been composited.

        Returns:
            Dictionary with composite verification results
        """
        pairs = find_overlay_pairs(self.output_dir)

        # Separate by type
        image_pairs = [p for p in pairs if p['media_type'] == 'image']
        video_pairs = [p for p in pairs if p['media_type'] == 'video']

        # Count composited
        composited_images = len([
            p for p in image_pairs
            if self.progress_tracker.is_composited(p['sid'], 'image')
        ])
        composited_videos = len([
            p for p in video_pairs
            if self.progress_tracker.is_composited(p['sid'], 'video')
        ])

        # Find missing and failed
        missing_list = []
        failed_list = []

        for pair in image_pairs:
            sid = pair['sid']
            if not self.progress_tracker.is_composited(sid, 'image'):
                fail_count = self.progress_tracker.get_composite_failure_count(sid, 'image')
                if fail_count > 0:
                    failed_list.append({
                        'file': pair['base_file'].name,
                        'type': 'image',
                        'attempts': fail_count,
                        'sid': sid
                    })
                else:
                    missing_list.append(f"{pair['base_file'].name} (image)")

        for pair in video_pairs:
            sid = pair['sid']
            if not self.progress_tracker.is_composited(sid, 'video'):
                fail_count = self.progress_tracker.get_composite_failure_count(sid, 'video')
                if fail_count > 0:
                    failed_list.append({
                        'file': pair['base_file'].name,
                        'type': 'video',
                        'attempts': fail_count,
                        'sid': sid
                    })
                else:
                    missing_list.append(f"{pair['base_file'].name} (video)")

        return {
            'total_pairs': len(pairs),
            'composited_images': composited_images,
            'composited_videos': composited_videos,
            'missing': len(missing_list),
            'missing_list': missing_list,
            'failed': len(failed_list),
            'failed_list': failed_list
        }

    def convert_all_to_local_timezone(self):
        """Convert all file timestamps and filenames from UTC to GPS-based timezone.

        This function:
        1. Scans all files in images/, videos/, overlays/, and composited/ folders
        2. Uses download_progress.json to get UTC dates and GPS coordinates for each file
        3. Determines timezone from GPS coordinates (or falls back to system timezone)
        4. Renames files to use the determined timezone
        5. Updates file modification/creation timestamps to match
        6. Tracks conversion status and timezone in progress file
        """
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Converting files from UTC to GPS-based timezone...")

        # Check if GPS-based timezone lookup is available
        if HAS_TIMEZONE_LOOKUP:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] GPS-based timezone lookup: ENABLED")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Files will be converted to timezone based on GPS coordinates")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] GPS-based timezone lookup: DISABLED (install timezonefinder + pytz)")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Files will be converted to system timezone as fallback")

        # Get system timezone info for display
        local_dt, local_str = utc_to_local("2025-01-01 00:00:00 UTC")
        timezone_name = local_dt.tzname()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] System timezone: {timezone_name} (used as fallback)")

        # Initialize timezone fields for existing entries if missing
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking progress file for missing timezone fields...")
        updated_count = 0
        for sid in self.progress_tracker.progress.get('downloaded', {}).keys():
            entry = self.progress_tracker.progress['downloaded'][sid]
            if 'timezone_converted' not in entry:
                entry['timezone_converted'] = False
                updated_count += 1
            if 'local_date' not in entry:
                entry['local_date'] = None
                updated_count += 1
            if 'current_timezone' not in entry:
                entry['current_timezone'] = 'UTC'
                updated_count += 1
            if 'location' not in entry:
                entry['location'] = ''
                updated_count += 1

        # Also check composited files
        for media_type in ['images', 'videos']:
            for sid in self.progress_tracker.progress.get('composited', {}).get(media_type, {}).keys():
                if 'timezone_converted' not in self.progress_tracker.progress['composited'][media_type][sid]:
                    self.progress_tracker.progress['composited'][media_type][sid]['timezone_converted'] = False
                    self.progress_tracker.progress['composited'][media_type][sid]['local_date'] = None
                    updated_count += 1

        if updated_count > 0:
            self.progress_tracker.save_progress()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Initialized {updated_count} entries with timezone tracking fields")

        # Define folders to process
        folders = [
            self.output_dir / "images",
            self.output_dir / "videos",
            self.output_dir / "overlays",
            self.output_dir / "composited" / "images",
            self.output_dir / "composited" / "videos"
        ]

        total_files = 0
        converted_files = 0
        skipped_files = 0
        failed_files = 0

        for folder in folders:
            if not folder.exists():
                continue

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing {folder.relative_to(self.output_dir)}...")

            for file_path in folder.glob("*.*"):
                if file_path.is_file():
                    total_files += 1

                    # Extract SID from filename
                    sid_short = parse_filename_for_sid(file_path.name)
                    if not sid_short:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Could not parse SID from {file_path.name}")
                        failed_files += 1
                        continue

                    # Find full SID in progress file (match first 8 chars)
                    # For composited files, check both downloaded and composited sections
                    full_sid = None
                    utc_date = None
                    is_composited_file = "_composited" in file_path.stem

                    # First try to find in downloaded section
                    for sid in self.progress_tracker.progress['downloaded'].keys():
                        if sid.startswith(sid_short):
                            full_sid = sid
                            utc_date = self.progress_tracker.get_utc_date(full_sid)
                            break

                    if not full_sid:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: SID {sid_short} not found in progress file for {file_path.name}")
                        failed_files += 1
                        continue

                    # Check if already converted
                    # For composited files, also check if it's marked in the composited section
                    already_converted = False
                    if is_composited_file:
                        # Check composited section for timezone conversion tracking
                        media_type_key = 'images' if 'images' in str(folder) else 'videos'
                        composited_dict = self.progress_tracker.progress.get('composited', {}).get(media_type_key, {})
                        if sid_short in composited_dict:
                            already_converted = composited_dict[sid_short].get('timezone_converted', False)
                    else:
                        already_converted = self.progress_tracker.is_timezone_converted(full_sid)

                    if already_converted:
                        skipped_files += 1
                        continue

                    # Get UTC date from progress file
                    if not utc_date:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: No UTC date found for SID {sid_short}")
                        failed_files += 1
                        continue

                    # Get location from progress file
                    location_str = self.progress_tracker.get_location(full_sid)

                    # Determine timezone based on GPS coordinates
                    target_timezone = None
                    timezone_source = 'system'

                    if location_str and HAS_TIMEZONE_LOOKUP:
                        coords = parse_location({'location': location_str})
                        if coords:
                            lat, lon = coords
                            target_timezone = get_timezone_from_coordinates(lat, lon)
                            if target_timezone:
                                timezone_source = 'gps'

                    # If no GPS timezone found, fallback to system
                    if not target_timezone:
                        target_timezone = 'system'

                    # Determine file type and suffix
                    media_type = self.progress_tracker.progress['downloaded'][full_sid].get('media_type', 'Image')
                    suffix = ""
                    if "_overlay" in file_path.stem:
                        suffix = "_overlay"
                    elif "_composited" in file_path.stem:
                        suffix = "_composited"

                    # Generate new filename with GPS-based timezone
                    extension = file_path.suffix[1:]  # Remove the dot
                    new_filename = generate_local_filename(
                        utc_date, media_type, sid_short, extension, suffix, target_timezone
                    )
                    new_path = file_path.parent / new_filename

                    # Skip if filename hasn't changed (already in correct timezone or same as UTC)
                    if new_path == file_path:
                        # Still update timestamps
                        convert_file_timestamps_to_local(file_path, utc_date, self.has_pywin32, target_timezone)

                        # Mark as converted with the target timezone
                        _, local_date_str = utc_to_timezone(utc_date, target_timezone) if target_timezone != 'system' else utc_to_local(utc_date)
                        if is_composited_file:
                            # Mark composited file as converted in its section
                            media_type_key = 'images' if 'images' in str(folder) else 'videos'
                            if sid_short in self.progress_tracker.progress.get('composited', {}).get(media_type_key, {}):
                                self.progress_tracker.progress['composited'][media_type_key][sid_short]['timezone_converted'] = True
                                self.progress_tracker.progress['composited'][media_type_key][sid_short]['local_date'] = local_date_str
                                self.progress_tracker.save_progress()
                        else:
                            self.progress_tracker.update_current_timezone(full_sid, target_timezone, local_date_str)

                        converted_files += 1
                        continue

                    # Rename file
                    try:
                        file_path.rename(new_path)

                        # Update file timestamps with GPS-based timezone
                        convert_file_timestamps_to_local(new_path, utc_date, self.has_pywin32, target_timezone)

                        # Mark as converted in progress file with the target timezone
                        _, local_date_str = utc_to_timezone(utc_date, target_timezone) if target_timezone != 'system' else utc_to_local(utc_date)
                        if is_composited_file:
                            # Mark composited file as converted in its section
                            media_type_key = 'images' if 'images' in str(folder) else 'videos'
                            if sid_short in self.progress_tracker.progress.get('composited', {}).get(media_type_key, {}):
                                self.progress_tracker.progress['composited'][media_type_key][sid_short]['timezone_converted'] = True
                                self.progress_tracker.progress['composited'][media_type_key][sid_short]['local_date'] = local_date_str
                                self.progress_tracker.save_progress()
                        else:
                            self.progress_tracker.update_current_timezone(full_sid, target_timezone, local_date_str)

                        converted_files += 1

                        if converted_files % 50 == 0:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Progress: {converted_files} converted, {skipped_files} skipped, {failed_files} failed")

                    except Exception as e:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Failed to convert {file_path.name}: {e}")
                        failed_files += 1

        # Print summary
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Timezone Conversion Complete!")
        print(f"{'='*60}")
        print(f"Total files processed: {total_files}")
        print(f"Converted: {converted_files}")
        print(f"Skipped (already converted): {skipped_files}")
        print(f"Failed: {failed_files}")
        print(f"{'='*60}\n")
