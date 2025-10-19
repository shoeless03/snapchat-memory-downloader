#!/usr/bin/env python3
"""
Snapchat Memories Downloader

This script downloads all Snapchat memories from the HTML export file,
organizing them with proper timestamps and tracking progress.
"""

import os
import re
import json
import time
import zipfile
import requests
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
from typing import List, Dict, Tuple
from urllib.parse import urlparse, parse_qs


class MemoriesParser(HTMLParser):
    """Parse the Snapchat memories HTML file to extract download links and metadata."""

    def __init__(self):
        super().__init__()
        self.memories = []
        self.current_row = {}
        self.current_tag = None
        self.td_count = 0
        self.in_table_row = False

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_table_row = True
            self.current_row = {}
            self.td_count = 0
        elif tag == 'td' and self.in_table_row:
            self.current_tag = 'td'
        elif tag == 'a' and self.in_table_row:
            attrs_dict = dict(attrs)
            onclick = attrs_dict.get('onclick', '')

            # Extract URL from onclick="downloadMemories('URL', this, true)"
            match = re.search(r"downloadMemories\('(.+?)',\s*this,\s*(true|false)\)", onclick)
            if match:
                self.current_row['download_url'] = match.group(1)

    def handle_data(self, data):
        if self.current_tag == 'td' and self.in_table_row:
            data = data.strip()
            if data and data not in ['Download', 'Downloaded']:
                if self.td_count == 0:  # Date column
                    self.current_row['date'] = data
                elif self.td_count == 1:  # Media Type column
                    self.current_row['media_type'] = data
                elif self.td_count == 2:  # Location column
                    self.current_row['location'] = data

    def handle_endtag(self, tag):
        if tag == 'td':
            self.td_count += 1
            self.current_tag = None
        elif tag == 'tr' and self.in_table_row:
            self.in_table_row = False
            if 'download_url' in self.current_row and 'date' in self.current_row:
                # Extract SID from URL for unique identification
                parsed = urlparse(self.current_row['download_url'])
                params = parse_qs(parsed.query)
                if 'sid' in params:
                    self.current_row['sid'] = params['sid'][0]
                    self.memories.append(self.current_row.copy())


class SnapchatDownloader:
    """Download and organize Snapchat memories."""

    def __init__(self, html_file: str, output_dir: str = "memories", progress_file: str = "download_progress.json"):
        self.html_file = html_file
        self.output_dir = Path(output_dir)
        self.progress_file = progress_file
        self.progress = self._load_progress()
        self.session = requests.Session()

        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "overlays").mkdir(exist_ok=True)

    def _load_progress(self) -> Dict:
        """Load download progress from JSON file."""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'downloaded': {}, 'failed': {}}

    def _save_progress(self):
        """Save download progress to JSON file."""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def parse_html(self) -> List[Dict]:
        """Parse the HTML file and extract all memories."""
        print(f"Parsing {self.html_file}...")

        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = MemoriesParser()
        parser.feed(html_content)

        print(f"Found {len(parser.memories)} memories to download")
        return parser.memories

    def _format_filename(self, memory: Dict, extension: str, is_overlay: bool = False) -> str:
        """Create a filename from the memory metadata."""
        # Parse date: "2025-10-16 19:47:03 UTC"
        date_str = memory['date'].replace(' UTC', '')
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        # Format: YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext
        # More readable with dashes in date and capitalized type
        date_part = dt.strftime('%Y-%m-%d')
        time_part = dt.strftime('%H%M%S')
        media_type = memory['media_type'].capitalize()  # "Image" or "Video"
        sid_short = memory['sid'][:8]  # Use first 8 chars of SID for brevity

        if is_overlay:
            return f"{date_part}_{time_part}_{media_type}_{sid_short}_overlay.png"
        else:
            return f"{date_part}_{time_part}_{media_type}_{sid_short}.{extension}"

    def download_memory(self, memory: Dict, retry_delay: float = 5.0) -> Tuple[bool, str]:
        """Download a single memory with retry logic for rate limiting."""
        sid = memory['sid']

        # Check if already downloaded
        if sid in self.progress['downloaded']:
            return True, "Already downloaded"

        # Check if previously failed
        if sid in self.progress['failed']:
            fail_count = self.progress['failed'][sid].get('count', 0)
            if fail_count >= 5:  # Increased from 3 to 5
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

        # If all retries failed, record the failure
        return self._record_failure(sid, memory, "Max retries exceeded")

    def _attempt_download(self, memory: Dict, sid: str) -> Tuple[bool, str]:
        """Single download attempt."""
        try:
            # Download the ZIP file
            response = self.session.get(memory['download_url'], timeout=60)

            # Check for rate limiting BEFORE raise_for_status
            if response.status_code == 429:
                raise ValueError(f"HTTP 429 Too Many Requests - Rate limited by server")

            response.raise_for_status()

            # Check if we got an HTML error page (rate limiting or errors)
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                raise ValueError(f"Received HTML error page instead of media (likely rate limited or error)")

            # Save to temporary file (could be ZIP, video, or image)
            temp_file = self.output_dir / f"temp_{sid}.download"
            with open(temp_file, 'wb') as f:
                f.write(response.content)

            # Check if it's a ZIP file or direct media file
            if zipfile.is_zipfile(temp_file):
                # It's a ZIP - extract normally
                temp_file.rename(self.output_dir / f"temp_{sid}.zip")
                temp_zip = self.output_dir / f"temp_{sid}.zip"
                self._extract_and_save_zip(temp_zip, memory, sid)
                temp_zip.unlink()
            else:
                # Not a ZIP - check if it's a direct media file
                media_type = self._detect_media_type(temp_file, content_type)
                if media_type:
                    # It's a direct media file (video or image)
                    self._save_direct_media(temp_file, memory, sid, media_type)
                    temp_file.unlink()
                else:
                    # Unknown file type - save for inspection
                    bad_file = self.output_dir / f"bad_{sid}.dat"
                    temp_file.rename(bad_file)
                    raise ValueError(f"Downloaded file is not a ZIP or recognized media. Saved to {bad_file} for inspection.")

            # Mark as downloaded
            self.progress['downloaded'][sid] = {
                'date': memory['date'],
                'media_type': memory['media_type'],
                'timestamp': datetime.now().isoformat()
            }

            # Remove from failed list if present
            if sid in self.progress['failed']:
                del self.progress['failed'][sid]

            self._save_progress()
            return True, "Downloaded successfully"

        except Exception as e:
            return self._record_failure(sid, memory, str(e), e)

    def _detect_media_type(self, file_path: Path, content_type: str) -> str:
        """Detect if file is a video or image based on magic bytes and content type."""
        # Check content-type header first
        if 'video' in content_type:
            return 'video'
        elif 'image' in content_type:
            return 'image'

        # Check magic bytes (file signatures)
        with open(file_path, 'rb') as f:
            header = f.read(12)

        # Video signatures
        if header[4:8] == b'ftyp':  # MP4/MOV
            return 'video'
        elif header[:4] == b'RIFF' and header[8:12] == b'AVI ':  # AVI
            return 'video'
        elif header[:3] == b'\x1a\x45\xdf':  # WebM/MKV
            return 'video'

        # Image signatures
        elif header[:2] == b'\xff\xd8':  # JPEG
            return 'image'
        elif header[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
            return 'image'
        elif header[:2] in (b'II', b'MM'):  # TIFF
            return 'image'
        elif header[:6] in (b'GIF87a', b'GIF89a'):  # GIF
            return 'image'

        return None

    def _save_direct_media(self, temp_file: Path, memory: Dict, sid: str, media_type: str):
        """Save a direct media file (not in a ZIP)."""
        # Determine file extension from content
        with open(temp_file, 'rb') as f:
            header = f.read(12)

        # Determine extension
        if header[4:8] == b'ftyp':
            ext = 'mp4'
        elif header[:2] == b'\xff\xd8':
            ext = 'jpg'
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            ext = 'png'
        else:
            ext = 'mp4' if media_type == 'video' else 'jpg'

        # Determine output directory
        if media_type == 'video':
            output_subdir = self.output_dir / "videos"
        else:
            output_subdir = self.output_dir / "images"

        # Create filename
        new_filename = self._format_filename(memory, ext, is_overlay=False)
        output_path = output_subdir / new_filename

        # Copy file
        import shutil
        shutil.copy2(temp_file, output_path)

        # Set file timestamps to match the Snapchat date
        self._set_file_timestamps(output_path, memory)

    def _extract_and_save_zip(self, temp_zip: Path, memory: Dict, sid: str):
        """Extract and save files from a ZIP archive."""
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                filename = file_info.filename

                # Determine if this is the main file or overlay
                is_overlay = 'overlay' in filename

                # Get extension
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

                # Extract and rename
                with zip_ref.open(file_info) as source, open(output_path, 'wb') as target:
                    target.write(source.read())

                # Set file timestamps to match the Snapchat date
                self._set_file_timestamps(output_path, memory)

    def _set_file_timestamps(self, file_path: Path, memory: Dict):
        """Set file creation and modification times to match Snapchat date."""
        date_str = memory['date'].replace(' UTC', '')
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        timestamp = dt.timestamp()
        timestamp_ns = int(timestamp * 1_000_000_000)  # Convert to nanoseconds

        import platform
        system = platform.system()

        # Set modification and access time (works on all platforms)
        os.utime(file_path, (timestamp, timestamp))

        # Set creation/birth time (platform-specific)
        if system == 'Linux':
            # On Linux, try to set birth time using chattr (requires debugfs or newer kernel)
            # Note: This requires specific filesystem support (ext4, btrfs, xfs with newer kernels)
            try:
                # Try using os.utime with ns parameter (Python 3.3+, Linux 3.5+)
                # This may set birth time on supported filesystems
                os.utime(file_path, ns=(timestamp_ns, timestamp_ns))
            except (OSError, AttributeError):
                # Birth time setting not supported, modification time is enough
                pass

        elif system == 'Darwin':  # macOS
            # On macOS, birth time is automatically set when file is created
            # We can't modify it after creation, but modification time works
            pass

        elif system == 'Windows':
            # On Windows, set creation time using pywin32
            try:
                import pywintypes
                import win32file
                import win32con

                # Convert to Windows FILETIME
                wintime = pywintypes.Time(dt)

                # Open file handle
                handle = win32file.CreateFile(
                    str(file_path),
                    win32con.GENERIC_WRITE,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    win32con.FILE_ATTRIBUTE_NORMAL,
                    None
                )

                # Set creation time
                win32file.SetFileTime(handle, wintime, None, None)
                handle.close()
            except ImportError:
                # pywin32 not installed, skip setting creation time
                pass
            except Exception:
                # If setting creation time fails, that's okay
                pass

    def _record_failure(self, sid: str, memory: Dict, error_msg: str, exception: Exception = None) -> Tuple[bool, str]:
        """Record a failed download attempt."""
        if sid not in self.progress['failed']:
            self.progress['failed'][sid] = {'count': 0, 'errors': [], 'url': memory['download_url']}

        self.progress['failed'][sid]['count'] += 1
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        }
        if exception:
            error_record['error_type'] = type(exception).__name__

        self.progress['failed'][sid]['errors'].append(error_record)
        self._save_progress()

        # Clean up temp files if they exist (but not bad files we saved for inspection)
        for temp_name in [f"temp_{sid}.zip", f"temp_{sid}.download"]:
            temp_file = self.output_dir / temp_name
            if temp_file.exists():
                temp_file.unlink()

        return False, f"Error: {error_msg}"

    def download_all(self, delay: float = 1.0):
        """Download all memories with progress tracking."""
        memories = self.parse_html()

        total = len(memories)
        already_downloaded = len([m for m in memories if m['sid'] in self.progress['downloaded']])
        to_download = total - already_downloaded

        print(f"\nTotal memories: {total}")
        print(f"Already downloaded: {already_downloaded}")
        print(f"To download: {to_download}\n")

        if to_download == 0:
            print("All memories already downloaded!")
            return

        downloaded_count = 0
        failed_count = 0
        skipped_count = 0

        for i, memory in enumerate(memories, 1):
            sid = memory['sid']

            if sid in self.progress['downloaded']:
                print(f"[{i}/{total}] Skipping {sid[:8]}... (already downloaded)")
                skipped_count += 1
                continue

            print(f"[{i}/{total}] Downloading {memory['date']} - {memory['media_type']}...", end=" ")

            success, message = self.download_memory(memory)
            print(message)

            if success:
                downloaded_count += 1
            else:
                failed_count += 1

            # Rate limiting
            if i < total:
                time.sleep(delay)

        print(f"\n{'='*60}")
        print(f"Download complete!")
        print(f"Downloaded: {downloaded_count}")
        print(f"Failed: {failed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total: {total}")
        print(f"{'='*60}\n")

        if failed_count > 0:
            print(f"Failed downloads are tracked in {self.progress_file}")
            print("Run the script again to retry failed downloads.")

    def update_existing_files(self):
        """Rename existing files to new format and update timestamps."""
        memories = self.parse_html()

        print("\nUpdating existing files...")
        updated_count = 0

        for memory in memories:
            sid = memory['sid']

            # Only process files that were already downloaded
            if sid not in self.progress['downloaded']:
                continue

            # Find old files by searching for the sid in filenames
            old_files = []
            for subdir in ['images', 'videos', 'overlays']:
                dir_path = self.output_dir / subdir
                if dir_path.exists():
                    for file in dir_path.glob(f"*{sid[:8]}*"):
                        old_files.append(file)

            if not old_files:
                continue

            # Rename each file found
            for old_file in old_files:
                # Determine if overlay
                is_overlay = 'overlay' in old_file.name

                # Get extension
                ext = old_file.suffix[1:]  # Remove the dot

                # Generate new filename
                new_filename = self._format_filename(memory, ext, is_overlay)
                new_path = old_file.parent / new_filename

                # Skip if already named correctly
                if old_file.name == new_filename:
                    # Just update timestamps
                    try:
                        self._set_file_timestamps(old_file, memory)
                        print(f"  Updated timestamps: {old_file.name}")
                        updated_count += 1
                    except Exception as e:
                        print(f"  Error updating timestamps for {old_file.name}: {e}")
                    continue

                # Rename file
                try:
                    old_file.rename(new_path)
                    print(f"  Renamed: {old_file.name} -> {new_filename}")

                    # Update timestamps
                    self._set_file_timestamps(new_path, memory)
                    updated_count += 1
                except Exception as e:
                    print(f"  Error renaming {old_file.name}: {e}")

        print(f"\nUpdated {updated_count} files")

    def verify_downloads(self) -> Dict:
        """Verify all downloads are complete."""
        memories = self.parse_html()

        results = {
            'total': len(memories),
            'downloaded': 0,
            'missing': [],
            'failed': []
        }

        for memory in memories:
            sid = memory['sid']
            if sid in self.progress['downloaded']:
                results['downloaded'] += 1
            elif sid in self.progress['failed']:
                results['failed'].append({
                    'sid': sid,
                    'date': memory['date'],
                    'attempts': self.progress['failed'][sid]['count']
                })
            else:
                results['missing'].append({
                    'sid': sid,
                    'date': memory['date']
                })

        return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Download Snapchat memories from HTML export')
    parser.add_argument('--html', default='data from snapchat/html/memories_history.html',
                        help='Path to memories_history.html file')
    parser.add_argument('--output', default='memories',
                        help='Output directory for downloaded memories')
    parser.add_argument('--delay', type=float, default=2.0,
                        help='Delay between downloads in seconds (default: 2.0, increase if rate limited)')
    parser.add_argument('--verify', action='store_true',
                        help='Verify downloads without downloading')
    parser.add_argument('--update-filenames', action='store_true',
                        help='Update existing files to new naming format and set timestamps')

    args = parser.parse_args()

    downloader = SnapchatDownloader(args.html, args.output)

    if args.update_filenames:
        downloader.update_existing_files()
    elif args.verify:
        print("Verifying downloads...")
        results = downloader.verify_downloads()

        print(f"\nVerification Results:")
        print(f"{'='*60}")
        print(f"Total memories: {results['total']}")
        print(f"Downloaded: {results['downloaded']}")
        print(f"Missing: {len(results['missing'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"{'='*60}\n")

        if results['missing']:
            print("Missing memories:")
            for item in results['missing'][:10]:
                print(f"  - {item['date']} (SID: {item['sid'][:8]}...)")
            if len(results['missing']) > 10:
                print(f"  ... and {len(results['missing']) - 10} more")

        if results['failed']:
            print("\nFailed memories:")
            for item in results['failed'][:10]:
                print(f"  - {item['date']} (SID: {item['sid'][:8]}..., {item['attempts']} attempts)")
            if len(results['failed']) > 10:
                print(f"  ... and {len(results['failed']) - 10} more")
    else:
        downloader.download_all(delay=args.delay)


if __name__ == '__main__':
    main()
