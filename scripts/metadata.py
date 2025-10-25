"""
File metadata operations (timestamps and GPS) for Snapchat memories.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple


def set_file_timestamps(file_path: Path, memory: Dict, has_pywin32: bool):
    """Set file creation and modification times to match Snapchat date.

    Args:
        file_path: Path to the file to update
        memory: Memory dictionary containing 'date' field
        has_pywin32: Whether pywin32 is available (Windows only)
    """
    date_str = memory['date'].replace(' UTC', '')
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    timestamp = dt.timestamp()
    timestamp_ns = int(timestamp * 1_000_000_000)  # Convert to nanoseconds

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
        if has_pywin32:
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


def parse_location(memory: Dict) -> Optional[Tuple[float, float]]:
    """Parse latitude and longitude from location string.

    Args:
        memory: Memory dictionary containing 'location' field

    Returns:
        Tuple of (latitude, longitude) or None if not available
    """
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


def add_gps_metadata(file_path: Path, memory: Dict, has_exiftool: bool):
    """Add GPS coordinates to file metadata using exiftool.

    Args:
        file_path: Path to the file to update
        memory: Memory dictionary containing 'location' field
        has_exiftool: Whether exiftool is available
    """
    if not has_exiftool:
        return

    coords = parse_location(memory)
    if not coords:
        return

    lat, lon = coords
    file_ext = file_path.suffix.lower()

    # Only process media files (skip overlays which are PNGs without location context)
    if file_ext not in ['.jpg', '.jpeg', '.mp4', '.mov', '.avi']:
        return

    # Use exiftool for all media types (images and videos)
    try:
        # Find exiftool using the config helper
        from snap_config import get_exiftool_path
        exiftool_cmd = get_exiftool_path()
        if not exiftool_cmd:
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


def copy_metadata_with_exiftool(source_file: Path, dest_file: Path, has_exiftool: bool):
    """Copy all metadata from source to destination using exiftool.

    Args:
        source_file: Source file with metadata
        dest_file: Destination file to copy metadata to
        has_exiftool: Whether exiftool is available
    """
    if not has_exiftool:
        return

    try:
        # Find exiftool using the config helper
        from snap_config import get_exiftool_path
        exiftool_cmd = get_exiftool_path()
        if not exiftool_cmd:
            return

        # Copy all metadata from source to dest
        result = subprocess.run([
            exiftool_cmd,
            '-TagsFromFile', str(source_file),
            '-all:all',
            '-overwrite_original',
            '-q',
            str(dest_file)
        ], capture_output=True, timeout=30, text=True)

    except Exception:
        pass


def update_existing_file_metadata(output_dir: Path, memory: Dict, sid: str, has_exiftool: bool, has_pywin32: bool):
    """Update metadata (timestamps and GPS) on already downloaded files.

    Args:
        output_dir: Base output directory
        memory: Memory dictionary
        sid: Session ID
        has_exiftool: Whether exiftool is available
        has_pywin32: Whether pywin32 is available
    """
    # Find files by searching for the sid in filenames
    for subdir in ['images', 'videos', 'overlays']:
        dir_path = output_dir / subdir
        if dir_path.exists():
            for file in dir_path.glob(f"*{sid[:8]}*"):
                try:
                    set_file_timestamps(file, memory, has_pywin32)
                    add_gps_metadata(file, memory, has_exiftool)
                except Exception:
                    pass
