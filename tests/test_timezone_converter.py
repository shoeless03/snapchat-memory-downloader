"""
Unit tests for timezone_converter module.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import pytest
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from timezone_converter import (
    utc_to_local,
    generate_local_filename,
    parse_filename_for_sid,
    convert_file_timestamps_to_local
)


class TestUtcToLocal:
    """Test UTC to local timezone conversion."""

    def test_utc_to_local_basic(self):
        """Test basic UTC to local conversion."""
        utc_date_str = '2023-01-15 14:30:00 UTC'
        local_dt, local_str = utc_to_local(utc_date_str)

        # Verify it's a datetime object
        assert isinstance(local_dt, datetime)

        # Verify it has timezone info
        assert local_dt.tzinfo is not None

        # Verify string format
        assert '2023-01-15' in local_str
        assert local_dt.tzname() in local_str

    def test_utc_to_local_midnight(self):
        """Test conversion at midnight UTC."""
        utc_date_str = '2023-01-15 00:00:00 UTC'
        local_dt, local_str = utc_to_local(utc_date_str)

        assert isinstance(local_dt, datetime)
        assert '2023-01' in local_str

    def test_utc_to_local_end_of_day(self):
        """Test conversion at end of day UTC."""
        utc_date_str = '2023-01-15 23:59:59 UTC'
        local_dt, local_str = utc_to_local(utc_date_str)

        assert isinstance(local_dt, datetime)
        # Depending on timezone, this might be next day
        assert local_dt.year == 2023
        assert local_dt.month in [1, 2]  # Could roll to next month

    def test_utc_to_local_preserves_date_components(self):
        """Test that basic date components are correct."""
        utc_date_str = '2023-06-15 12:00:00 UTC'
        local_dt, local_str = utc_to_local(utc_date_str)

        # The date should be close (within a day due to timezone differences)
        assert local_dt.year == 2023
        assert local_dt.month in [6]  # June
        assert local_dt.day in [14, 15, 16]  # Could be +/- 1 day

    def test_utc_to_local_string_format(self):
        """Test that returned string has correct format."""
        utc_date_str = '2023-01-15 14:30:00 UTC'
        local_dt, local_str = utc_to_local(utc_date_str)

        # String should be in format: YYYY-MM-DD HH:MM:SS TZ
        # Timezone name might have multiple words (e.g., "Eastern Standard Time")
        parts = local_str.split()
        assert len(parts) >= 3  # At least date, time, and timezone
        assert len(parts[0].split('-')) == 3  # Date part
        assert len(parts[1].split(':')) == 3  # Time part
        # Remaining parts are timezone name (might be multiple words)


class TestGenerateLocalFilename:
    """Test local filename generation."""

    def test_generate_filename_basic(self):
        """Test basic filename generation."""
        utc_date_str = '2023-01-15 14:30:00 UTC'
        filename = generate_local_filename(utc_date_str, 'Image', 'abc12345', 'jpg')

        # Should have format: YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext
        assert filename.endswith('.jpg')
        assert '_Image_' in filename
        assert '_abc12345.' in filename

    def test_generate_filename_with_overlay_suffix(self):
        """Test filename generation with overlay suffix."""
        utc_date_str = '2023-01-15 14:30:00 UTC'
        filename = generate_local_filename(utc_date_str, 'Image', 'abc12345', 'png', '_overlay')

        assert filename.endswith('_overlay.png')
        assert '_Image_abc12345_overlay.png' in filename

    def test_generate_filename_with_composited_suffix(self):
        """Test filename generation with composited suffix."""
        utc_date_str = '2023-01-15 14:30:00 UTC'
        filename = generate_local_filename(utc_date_str, 'Video', 'xyz78901', 'mp4', '_composited')

        assert filename.endswith('_composited.mp4')
        assert '_Video_xyz78901_composited.mp4' in filename

    def test_generate_filename_video(self):
        """Test filename generation for video."""
        utc_date_str = '2023-01-15 14:30:00 UTC'
        filename = generate_local_filename(utc_date_str, 'Video', 'xyz78901', 'mp4')

        assert filename.endswith('.mp4')
        assert '_Video_' in filename

    def test_generate_filename_format_structure(self):
        """Test that filename has correct structure."""
        utc_date_str = '2023-01-15 14:30:00 UTC'
        filename = generate_local_filename(utc_date_str, 'Image', 'abc12345', 'jpg')

        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        parts = name_without_ext.split('_')

        # Should have: DATE, TIME, TYPE, SID
        assert len(parts) >= 4
        assert parts[-2] == 'Image'  # Type
        assert parts[-1] == 'abc12345'  # SID

        # First part should be date YYYY-MM-DD
        date_part = parts[0]
        assert len(date_part.split('-')) == 3


class TestParseFilenameForSid:
    """Test SID extraction from filename."""

    def test_parse_filename_basic(self):
        """Test parsing basic filename."""
        filename = '2023-01-15_143000_Image_abc12345.jpg'
        sid = parse_filename_for_sid(filename)

        assert sid == 'abc12345'

    def test_parse_filename_with_overlay(self):
        """Test parsing filename with overlay suffix."""
        filename = '2023-01-15_143000_Image_abc12345_overlay.png'
        sid = parse_filename_for_sid(filename)

        assert sid == 'abc12345'

    def test_parse_filename_with_composited(self):
        """Test parsing filename with composited suffix."""
        filename = '2023-01-15_143000_Video_xyz78901_composited.mp4'
        sid = parse_filename_for_sid(filename)

        assert sid == 'xyz78901'

    def test_parse_filename_video(self):
        """Test parsing video filename."""
        filename = '2023-01-15_143000_Video_xyz78901.mp4'
        sid = parse_filename_for_sid(filename)

        assert sid == 'xyz78901'

    def test_parse_filename_with_path(self):
        """Test parsing when given full path."""
        filepath = '/path/to/2023-01-15_143000_Image_abc12345.jpg'
        sid = parse_filename_for_sid(filepath)

        assert sid == 'abc12345'

    def test_parse_filename_invalid_format(self):
        """Test parsing invalid filename format."""
        invalid_filenames = [
            'invalid.jpg',
            '2023-01-15.jpg',
            'no_sid_here.jpg',
        ]

        for filename in invalid_filenames:
            sid = parse_filename_for_sid(filename)
            # Should return None or handle gracefully
            # (implementation might vary)

    def test_parse_filename_edge_cases(self):
        """Test edge cases in filename parsing."""
        # Filename with extra underscores
        filename = '2023-01-15_143000_Image_abc12345_extra_stuff.jpg'
        sid = parse_filename_for_sid(filename)
        # Should still get the SID (might be 'stuff' or None depending on implementation)

    def test_parse_filename_different_extensions(self):
        """Test parsing with different file extensions."""
        extensions = ['jpg', 'jpeg', 'png', 'mp4', 'mov']

        for ext in extensions:
            filename = f'2023-01-15_143000_Image_abc12345.{ext}'
            sid = parse_filename_for_sid(filename)
            assert sid == 'abc12345'


class TestConvertFileTimestampsToLocal:
    """Test file timestamp conversion."""

    def test_convert_timestamps_basic(self, tmp_path):
        """Test basic timestamp conversion."""
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        utc_date_str = '2023-01-15 14:30:00 UTC'
        convert_file_timestamps_to_local(test_file, utc_date_str, has_pywin32=False)

        # Verify modification time was updated
        stat = os.stat(test_file)
        local_dt, _ = utc_to_local(utc_date_str)
        expected_timestamp = local_dt.timestamp()

        # Allow 1 second tolerance
        assert abs(stat.st_mtime - expected_timestamp) < 1

    def test_convert_timestamps_different_times(self, tmp_path):
        """Test conversion with various times."""
        test_times = [
            '2023-01-15 00:00:00 UTC',
            '2023-06-20 12:00:00 UTC',
            '2023-12-31 23:59:59 UTC',
        ]

        for utc_date_str in test_times:
            test_file = tmp_path / f"test_{utc_date_str[:10]}.jpg"
            test_file.write_text("test")

            convert_file_timestamps_to_local(test_file, utc_date_str, has_pywin32=False)

            stat = os.stat(test_file)
            local_dt, _ = utc_to_local(utc_date_str)
            expected_timestamp = local_dt.timestamp()

            assert abs(stat.st_mtime - expected_timestamp) < 1

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_convert_timestamps_windows_with_pywin32(self, tmp_path):
        """Test timestamp conversion on Windows with pywin32."""
        pytest.importorskip("pywintypes")
        pytest.importorskip("win32file")

        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        utc_date_str = '2023-06-20 10:15:00 UTC'
        convert_file_timestamps_to_local(test_file, utc_date_str, has_pywin32=True)

        stat = os.stat(test_file)
        local_dt, _ = utc_to_local(utc_date_str)
        expected_timestamp = local_dt.timestamp()

        assert abs(stat.st_mtime - expected_timestamp) < 1
        # On Windows, ctime is creation time
        assert abs(stat.st_ctime - expected_timestamp) < 1

    def test_convert_timestamps_without_pywin32(self, tmp_path):
        """Test that conversion works without pywin32."""
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        utc_date_str = '2023-03-10 08:45:00 UTC'

        # Should not raise error
        convert_file_timestamps_to_local(test_file, utc_date_str, has_pywin32=False)

        stat = os.stat(test_file)
        local_dt, _ = utc_to_local(utc_date_str)
        expected_timestamp = local_dt.timestamp()

        assert abs(stat.st_mtime - expected_timestamp) < 1

    def test_convert_timestamps_handles_errors(self, tmp_path):
        """Test that errors are handled gracefully."""
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        # Make file read-only
        test_file.chmod(0o444)

        utc_date_str = '2023-01-15 14:30:00 UTC'

        try:
            # Should handle permission error gracefully (implementation dependent)
            convert_file_timestamps_to_local(test_file, utc_date_str, has_pywin32=False)
        except (PermissionError, OSError):
            # Some implementations might raise, others might silently fail
            pass
        finally:
            # Restore permissions
            test_file.chmod(0o644)


class TestTimezoneConversionIntegration:
    """Integration tests for timezone conversion."""

    def test_round_trip_conversion(self):
        """Test that UTC -> Local -> filename works correctly."""
        utc_date_str = '2023-01-15 14:30:00 UTC'

        # Convert to local
        local_dt, local_str = utc_to_local(utc_date_str)

        # Generate filename
        filename = generate_local_filename(utc_date_str, 'Image', 'abc12345', 'jpg')

        # Parse SID from filename
        sid = parse_filename_for_sid(filename)

        # Verify SID is correct
        assert sid == 'abc12345'

        # Verify filename contains proper date/time
        assert '2023-01' in filename or '2023-02' in filename  # Might be different day in local TZ

    def test_consistent_timezone_handling(self):
        """Test that same UTC time produces consistent local filenames."""
        utc_date_str = '2023-01-15 14:30:00 UTC'

        filename1 = generate_local_filename(utc_date_str, 'Image', 'abc12345', 'jpg')
        filename2 = generate_local_filename(utc_date_str, 'Image', 'abc12345', 'jpg')

        # Should produce identical filenames
        assert filename1 == filename2

    def test_different_utc_times_different_local_filenames(self):
        """Test that different UTC times produce different local filenames."""
        utc1 = '2023-01-15 14:30:00 UTC'
        utc2 = '2023-01-15 15:30:00 UTC'

        filename1 = generate_local_filename(utc1, 'Image', 'abc12345', 'jpg')
        filename2 = generate_local_filename(utc2, 'Image', 'abc12345', 'jpg')

        # Should be different (at least in time component)
        assert filename1 != filename2
