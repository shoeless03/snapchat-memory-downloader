"""
Timezone conversion utilities for Snapchat memories.

Converts file timestamps and filenames from UTC to local timezone.
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Optional


def utc_to_local(utc_date_str: str) -> Tuple[datetime, str]:
    """Convert UTC date string to local timezone.

    Args:
        utc_date_str: Date string in format "YYYY-MM-DD HH:MM:SS UTC"

    Returns:
        Tuple of (datetime object in local timezone, formatted string)
    """
    # Parse UTC date string
    date_str = utc_date_str.replace(' UTC', '')
    utc_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

    # Add UTC timezone info
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)

    # Convert to local timezone
    local_dt = utc_dt.astimezone()

    # Format as string (same format as UTC but with local timezone)
    local_str = local_dt.strftime('%Y-%m-%d %H:%M:%S') + f' {local_dt.tzname()}'

    return local_dt, local_str


def generate_local_filename(utc_date_str: str, media_type: str, sid_short: str, extension: str, suffix: str = "") -> str:
    """Generate filename with local timezone.

    Args:
        utc_date_str: Date string in format "YYYY-MM-DD HH:MM:SS UTC"
        media_type: "Image" or "Video"
        sid_short: First 8 characters of SID
        extension: File extension (without dot)
        suffix: Optional suffix like "_overlay" or "_composited"

    Returns:
        Filename in format: YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX{suffix}.ext
    """
    local_dt, _ = utc_to_local(utc_date_str)

    date_part = local_dt.strftime('%Y-%m-%d')
    time_part = local_dt.strftime('%H%M%S')

    return f"{date_part}_{time_part}_{media_type}_{sid_short}{suffix}.{extension}"


def parse_filename_for_sid(filename: str) -> Optional[str]:
    """Extract SID from filename.

    Args:
        filename: Filename in format YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext

    Returns:
        SID (8 character prefix) or None if not found
    """
    try:
        # Remove extension
        name = Path(filename).stem

        # Handle overlay and composited suffixes
        if name.endswith('_overlay'):
            name = name[:-8]
        elif name.endswith('_composited'):
            name = name[:-11]

        # Split by underscore and get last part (sid)
        parts = name.split('_')
        if len(parts) >= 4:
            return parts[-1]  # sidXXXXXXXX
    except Exception:
        pass

    return None


def convert_file_timestamps_to_local(file_path: Path, utc_date_str: str, has_pywin32: bool = False):
    """Update file modification and creation times to local timezone.

    Args:
        file_path: Path to file
        utc_date_str: Original UTC date string
        has_pywin32: Whether pywin32 is available (Windows only)
    """
    local_dt, _ = utc_to_local(utc_date_str)
    local_timestamp = local_dt.timestamp()

    # Set modification time (works on all platforms)
    os.utime(file_path, (local_timestamp, local_timestamp))

    # Set creation time (Windows only with pywin32)
    if has_pywin32 and os.name == 'nt':
        try:
            import pywintypes
            import win32file
            import win32con

            # Convert to Windows FILETIME format
            win_timestamp = pywintypes.Time(local_timestamp)

            # Open file handle
            handle = win32file.CreateFile(
                str(file_path),
                win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None
            )

            # Set creation time
            win32file.SetFileTime(handle, win_timestamp, None, None)
            handle.close()
        except Exception:
            pass  # Silently fail if pywin32 not available
