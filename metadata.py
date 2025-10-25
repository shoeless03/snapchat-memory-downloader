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

# Try to import timezone lookup libraries
try:
    from timezonefinder import TimezoneFinder
    import pytz
    HAS_TIMEZONE_LOOKUP = True
    _tf = TimezoneFinder()
except ImportError:
    HAS_TIMEZONE_LOOKUP = False
    _tf = None


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


def get_timezone_from_coordinates(lat: float, lon: float) -> Optional[str]:
    """Get timezone name from GPS coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Timezone name (e.g., 'America/New_York') or None if not found
    """
    if not HAS_TIMEZONE_LOOKUP or _tf is None:
        return None

    try:
        timezone_name = _tf.timezone_at(lat=lat, lng=lon)
        return timezone_name
    except Exception:
        return None


def utc_to_timezone(utc_date_str: str, timezone_name: str) -> Tuple[datetime, str]:
    """Convert UTC date string to specified timezone.

    Args:
        utc_date_str: UTC date string (e.g., "2025-10-16 19:47:03 UTC")
        timezone_name: Timezone name (e.g., 'America/New_York')

    Returns:
        Tuple of (datetime object in target timezone, formatted string)
    """
    # Parse UTC date
    date_str = utc_date_str.replace(' UTC', '')
    utc_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

    # Set UTC timezone
    utc_tz = pytz.UTC
    utc_dt = utc_tz.localize(utc_dt)

    # Convert to target timezone
    target_tz = pytz.timezone(timezone_name)
    local_dt = utc_dt.astimezone(target_tz)

    # Format as string (same format as input but with timezone)
    local_str = local_dt.strftime('%Y-%m-%d %H:%M:%S') + f' {timezone_name}'

    return local_dt, local_str


def get_timezone_for_memory(memory: Dict, fallback_to_system: bool = True) -> Tuple[Optional[str], Optional[str]]:
    """Get the appropriate timezone for a memory based on GPS coordinates.

    Args:
        memory: Memory dictionary containing 'location' field
        fallback_to_system: Whether to fallback to system timezone if GPS lookup fails

    Returns:
        Tuple of (timezone_name, source) where source is 'gps', 'system', or None
        Examples: ('America/New_York', 'gps'), ('America/Chicago', 'system'), (None, None)
    """
    # Try GPS-based lookup first
    coords = parse_location(memory)
    if coords and HAS_TIMEZONE_LOOKUP:
        lat, lon = coords
        timezone_name = get_timezone_from_coordinates(lat, lon)
        if timezone_name:
            return (timezone_name, 'gps')

    # Fallback to system timezone if requested
    if fallback_to_system:
        try:
            import time
            # Get system timezone name
            if hasattr(time, 'tzname'):
                # This gives abbreviated name like 'EST'
                # We need to convert to full timezone name
                from datetime import timezone
                import time
                # Get offset in seconds
                offset_seconds = -time.timezone if not time.daylight else -time.altzone

                # For system timezone, we'll use a simple approach
                # Try to get timezone from datetime
                local_dt = datetime.now().astimezone()
                timezone_name = local_dt.tzname()

                # If we have pytz, try to find the full timezone name
                if HAS_TIMEZONE_LOOKUP:
                    # Common timezone mappings for fallback
                    # In practice, this is hard to do perfectly without the timezone database
                    # So we'll just return 'system' as the timezone name
                    return ('system', 'system')
                else:
                    return ('system', 'system')
        except Exception:
            pass

    return (None, None)


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
        # Find exiftool
        exiftool_local = Path(__file__).parent / 'exiftool-13.39_64' / 'exiftool(-k).exe'
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
        # Find exiftool
        exiftool_local = Path(__file__).parent / 'exiftool-13.39_64' / 'exiftool(-k).exe'
        if exiftool_local.exists():
            exiftool_cmd = str(exiftool_local)
        elif shutil.which('exiftool') is not None:
            exiftool_cmd = 'exiftool'
        else:
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
