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
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse, parse_qs


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Import main and run it
    # Note: This needs to be at the top for readability, but main() is defined below
    pass  # Will be replaced at the end


# ============================================================================
# Main Function - Script Entry Point
# ============================================================================

def main():
    """Main entry point - parses arguments and orchestrates the download."""
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

    args = parser.parse_args()

    # Check dependencies before starting
    check_dependencies()

    # Create downloader instance
    downloader = SnapchatDownloader(args.html, args.output)

    # Run in verification mode or download mode
    if args.verify:
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
        # Download all memories
        downloader.download_all(delay=args.delay)


# ============================================================================
# Dependency Checking - Called First by main()
# ============================================================================

def check_dependencies():
    """Check for optional dependencies and prompt user."""
    import sys
    import platform
    import shutil
    from pathlib import Path as PathlibPath

    # Check for ExifTool
    script_dir = PathlibPath(__file__).parent
    if platform.system() == 'Windows':
        exiftool_local = script_dir / 'exiftool-13.39_64' / 'exiftool(-k).exe'
    else:
        exiftool_local = script_dir / 'exiftool'

    has_exiftool = exiftool_local.exists() or shutil.which('exiftool') is not None

    # Check for pywin32 (Windows only)
    has_pywin32 = True
    if platform.system() == 'Windows':
        try:
            import pywintypes
            import win32file
        except ImportError:
            has_pywin32 = False

    # Display dependency status
    missing_features = []

    if not has_exiftool:
        missing_features.append(("ExifTool", "GPS metadata embedding"))

    if not has_pywin32 and platform.system() == 'Windows':
        missing_features.append(("pywin32", "setting file creation dates on Windows"))

    if missing_features:
        print("\n" + "="*70)
        print("OPTIONAL DEPENDENCIES")
        print("="*70)
        print("\nThe following optional features are not available:\n")

        for dep, feature in missing_features:
            print(f"  • {dep}: Required for {feature}")

        print("\nInstallation instructions:")
        if not has_exiftool:
            print("\n  ExifTool:")
            print("    - Windows: Download from https://exiftool.org/")
            print("               Extract to this folder as 'exiftool-13.39_64/'")
            print("    - Linux:   sudo apt install libimage-exiftool-perl")
            print("    - macOS:   brew install exiftool")

        if not has_pywin32 and platform.system() == 'Windows':
            print("\n  pywin32:")
            print("    - Windows: pip install pywin32")

        print("\nWhat would you like to do?")
        print("  1. Continue without these features")
        print("  2. Quit to install dependencies (recommended)")
        print("="*70)

        while True:
            try:
                choice = input("\nEnter your choice (1 or 2): ").strip()
                if choice == '1':
                    print("\nContinuing with available features...")
                    if not has_exiftool:
                        print("  - GPS metadata will NOT be added to files")
                    if not has_pywin32 and platform.system() == 'Windows':
                        print("  - File creation dates will NOT be set (modification dates will still work)")
                    print("\nNOTE: You can install these dependencies later and re-run the script")
                    print("      to add GPS data and update timestamps on your existing files.")
                    print()
                    break
                elif choice == '2':
                    print("\nExiting. Please install the dependencies and run the script again.")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please enter 1 or 2.")
            except (KeyboardInterrupt, EOFError):
                print("\n\nExiting...")
                sys.exit(0)
    else:
        print("\n" + "="*70)
        print("All optional dependencies found!")
        print("  [OK] ExifTool: GPS metadata will be embedded")
        if platform.system() == 'Windows':
            print("  [OK] pywin32: File creation dates will be set")
        print("="*70 + "\n")


# ============================================================================
# SnapchatDownloader Class - Main Orchestrator
# ============================================================================

class SnapchatDownloader:
    """Download and organize Snapchat memories.

    Methods are organized in execution order - read from top to bottom
    to follow the flow of a typical download session.
    """

    # ========================================================================
    # Initialization - Called when instance is created
    # ========================================================================

    def __init__(self, html_file: str, output_dir: str = "memories", progress_file: str = "download_progress.json"):
        """Initialize the downloader with configuration and check dependencies."""
        self.html_file = html_file
        self.output_dir = Path(output_dir)
        self.progress_file = progress_file
        self.progress = self._load_progress()
        self.session = requests.Session()

        # Check for optional dependencies and set capabilities
        self.has_exiftool = self._check_exiftool()
        self.has_pywin32 = self._check_pywin32()

        # GPS metadata will be added automatically if ExifTool is available
        self.add_gps = self.has_exiftool

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

    def _check_exiftool(self) -> bool:
        """Check if ExifTool is available."""
        import shutil
        import platform
        from pathlib import Path as PathlibPath

        # Check for exiftool in local directory first, then PATH
        script_dir = PathlibPath(__file__).parent

        # Check different possible locations based on platform
        if platform.system() == 'Windows':
            exiftool_local = script_dir / 'exiftool-13.39_64' / 'exiftool(-k).exe'
        else:
            exiftool_local = script_dir / 'exiftool'

        return exiftool_local.exists() or shutil.which('exiftool') is not None

    def _check_pywin32(self) -> bool:
        """Check if pywin32 is available (Windows only)."""
        import platform
        if platform.system() != 'Windows':
            return True  # Not needed on non-Windows platforms

        try:
            import pywintypes
            import win32file
            return True
        except ImportError:
            return False

    # ========================================================================
    # Main Download Flow - download_all() orchestrates everything
    # ========================================================================

    def download_all(self, delay: float = 1.0):
        """Download all memories with progress tracking."""
        # Step 1: Parse HTML to get list of memories
        memories = self.parse_html()

        # Step 2: Calculate what needs to be downloaded
        total = len(memories)
        already_downloaded = len([m for m in memories if m['sid'] in self.progress['downloaded']])
        to_download = total - already_downloaded

        print(f"\nTotal memories: {total}")
        print(f"Already downloaded: {already_downloaded}")
        print(f"To download: {to_download}\n")

        if to_download == 0:
            print("All memories already downloaded!")
            return

        # Step 3: Download each memory
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

        # Step 4: Print summary
        print(f"\n{'='*60}")
        print(f"Download complete!")
        print(f"Downloaded: {downloaded_count}")
        print(f"Failed: {failed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total: {total}")
        print(f"{'='*60}\n")

        if failed_count > 0:
            print(f"Failed downloads are tracked in {self.progress_file}")
            print("Run the script again to retry failed downloads.\n")

        # Remind user about optional features
        if not self.has_exiftool or not self.has_pywin32:
            print("TIP: To add missing features to your downloaded files:")
            if not self.has_exiftool:
                print("  - Install ExifTool to add GPS metadata")
            if not self.has_pywin32:
                print("  - Install pywin32 to set file creation dates")
            print("  Then run the script again to update existing files")
            print()

    def parse_html(self) -> List[Dict]:
        """Parse the HTML file and extract all memories."""
        print(f"Parsing {self.html_file}...")

        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = MemoriesParser()
        parser.feed(html_content)

        print(f"Found {len(parser.memories)} memories to download")
        return parser.memories

    def download_memory(self, memory: Dict, retry_delay: float = 5.0) -> Tuple[bool, str]:
        """Download a single memory with retry logic for rate limiting."""
        sid = memory['sid']

        # Check if already downloaded - update metadata if needed
        if sid in self.progress['downloaded']:
            # Check if we should update metadata on existing files
            self._update_existing_file_metadata(memory, sid)
            return True, "Already downloaded"

        # Check if previously failed
        if sid in self.progress['failed']:
            fail_count = self.progress['failed'][sid].get('count', 0)
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

        # If all retries failed, record the failure
        return self._record_failure(sid, memory, "Max retries exceeded")

    def _attempt_download(self, memory: Dict, sid: str) -> Tuple[bool, str]:
        """Single download attempt."""
        try:
            # Download the file
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

            # Process the downloaded file (ZIP or direct media)
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

                # Add GPS metadata if available
                self._add_gps_metadata(output_path, memory)

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

        # Add GPS metadata if available
        self._add_gps_metadata(output_path, memory)

    def _format_filename(self, memory: Dict, extension: str, is_overlay: bool = False) -> str:
        """Create a filename from the memory metadata."""
        # Parse date: "2025-10-16 19:47:03 UTC"
        date_str = memory['date'].replace(' UTC', '')
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        # Format: YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext
        date_part = dt.strftime('%Y-%m-%d')
        time_part = dt.strftime('%H%M%S')
        media_type = memory['media_type'].capitalize()  # "Image" or "Video"
        sid_short = memory['sid'][:8]  # Use first 8 chars of SID for brevity

        if is_overlay:
            return f"{date_part}_{time_part}_{media_type}_{sid_short}_overlay.png"
        else:
            return f"{date_part}_{time_part}_{media_type}_{sid_short}.{extension}"

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
            # On Linux, try to set birth time
            try:
                os.utime(file_path, ns=(timestamp_ns, timestamp_ns))
            except (OSError, AttributeError):
                pass

        elif system == 'Darwin':  # macOS
            # On macOS, birth time is automatically set when file is created
            pass

        elif system == 'Windows':
            # On Windows, set creation time using pywin32 if available
            if self.has_pywin32:
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
                except Exception:
                    pass

    def _parse_location(self, memory: Dict) -> Optional[Tuple[float, float]]:
        """Parse latitude and longitude from location string."""
        if 'location' not in memory or not memory['location']:
            return None

        # Format: "Latitude, Longitude: 42.438072, -82.91975"
        location = memory['location']
        try:
            if 'Latitude, Longitude:' in location:
                coords = location.split('Latitude, Longitude:')[1].strip()
                lat_str, lon_str = coords.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
                return (lat, lon)
        except (ValueError, IndexError):
            return None

        return None

    def _add_gps_metadata(self, file_path: Path, memory: Dict):
        """Add GPS coordinates to file metadata using exiftool."""
        # Skip if GPS feature is not enabled
        if not self.add_gps:
            return

        coords = self._parse_location(memory)
        if not coords:
            return

        lat, lon = coords
        file_ext = file_path.suffix.lower()

        # Only process media files (skip overlays which are PNGs without location context)
        if file_ext not in ['.jpg', '.jpeg', '.mp4', '.mov', '.avi']:
            return

        # Use exiftool for all media types (images and videos)
        try:
            import subprocess
            import shutil
            from pathlib import Path as PathlibPath

            # Check for exiftool in local directory first, then PATH
            exiftool_local = PathlibPath(__file__).parent / 'exiftool-13.39_64' / 'exiftool(-k).exe'
            if exiftool_local.exists():
                exiftool_cmd = str(exiftool_local)
            elif shutil.which('exiftool') is not None:
                exiftool_cmd = 'exiftool'
            else:
                return

            # Format GPS coordinates for exiftool
            lat_ref = 'N' if lat >= 0 else 'S'
            lon_ref = 'E' if lon >= 0 else 'W'

            # Run exiftool to add GPS metadata
            result = subprocess.run([
                exiftool_cmd,
                f'-GPSLatitude={abs(lat)}',
                f'-GPSLatitudeRef={lat_ref}',
                f'-GPSLongitude={abs(lon)}',
                f'-GPSLongitudeRef={lon_ref}',
                '-overwrite_original',
                '-q',
                str(file_path)
            ], capture_output=True, timeout=30, text=True)

        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

    def _update_existing_file_metadata(self, memory: Dict, sid: str):
        """Update metadata (timestamps and GPS) on already downloaded files."""
        # Find files by searching for the sid in filenames
        for subdir in ['images', 'videos', 'overlays']:
            dir_path = self.output_dir / subdir
            if dir_path.exists():
                for file in dir_path.glob(f"*{sid[:8]}*"):
                    try:
                        self._set_file_timestamps(file, memory)
                        self._add_gps_metadata(file, memory)
                    except Exception:
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

        # Clean up temp files if they exist
        for temp_name in [f"temp_{sid}.zip", f"temp_{sid}.download"]:
            temp_file = self.output_dir / temp_name
            if temp_file.exists():
                temp_file.unlink()

        return False, f"Error: {error_msg}"

    # ========================================================================
    # Verification Flow - Alternative to download_all()
    # ========================================================================

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


# ============================================================================
# Helper Classes - Used by SnapchatDownloader
# ============================================================================

class MemoriesParser(HTMLParser):
    """Parse the Snapchat memories HTML file to extract download links and metadata.

    This class is used by SnapchatDownloader.parse_html() to extract memory
    information from the HTML export file.
    """

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


# ============================================================================
# Script Execution
# ============================================================================

if __name__ == '__main__':
    main()
