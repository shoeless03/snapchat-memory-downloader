"""
Unit tests for metadata module.
"""

import sys
import os
import platform
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from metadata import (
    set_file_timestamps,
    parse_location,
    add_gps_metadata,
    copy_metadata_with_exiftool,
    update_existing_file_metadata
)


class TestSetFileTimestamps:
    """Test setting file timestamps."""

    def test_set_timestamps_basic(self, tmp_path):
        """Test setting basic timestamps (modification/access)."""
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'date': '2023-01-15 14:30:00 UTC'}
        set_file_timestamps(test_file, memory, has_pywin32=False)

        # Verify modification time was set
        expected_dt = datetime.strptime('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
        expected_timestamp = expected_dt.timestamp()

        stat = os.stat(test_file)
        # Allow 1 second tolerance for file system differences
        assert abs(stat.st_mtime - expected_timestamp) < 1

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_set_timestamps_windows_with_pywin32(self, tmp_path):
        """Test setting creation time on Windows with pywin32."""
        pytest.importorskip("pywintypes")
        pytest.importorskip("win32file")

        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'date': '2023-06-20 10:15:00 UTC'}
        set_file_timestamps(test_file, memory, has_pywin32=True)

        # Verify timestamps were set
        stat = os.stat(test_file)
        expected_dt = datetime.strptime('2023-06-20 10:15:00', '%Y-%m-%d %H:%M:%S')
        expected_timestamp = expected_dt.timestamp()

        assert abs(stat.st_mtime - expected_timestamp) < 1
        # On Windows, ctime is creation time
        assert abs(stat.st_ctime - expected_timestamp) < 1

    def test_set_timestamps_without_pywin32(self, tmp_path):
        """Test that function works even without pywin32."""
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'date': '2023-03-10 08:45:00 UTC'}
        # Should not raise error even without pywin32
        set_file_timestamps(test_file, memory, has_pywin32=False)

        stat = os.stat(test_file)
        expected_dt = datetime.strptime('2023-03-10 08:45:00', '%Y-%m-%d %H:%M:%S')
        expected_timestamp = expected_dt.timestamp()
        assert abs(stat.st_mtime - expected_timestamp) < 1


class TestParseLocation:
    """Test GPS location parsing."""

    def test_parse_location_valid(self):
        """Test parsing valid GPS coordinates."""
        memory = {'location': 'Latitude, Longitude: 42.438072, -82.91975'}
        coords = parse_location(memory)

        assert coords is not None
        assert coords[0] == 42.438072  # latitude
        assert coords[1] == -82.91975  # longitude

    def test_parse_location_positive_coords(self):
        """Test parsing positive coordinates."""
        memory = {'location': 'Latitude, Longitude: 40.7128, -74.0060'}
        coords = parse_location(memory)

        assert coords == (40.7128, -74.0060)

    def test_parse_location_negative_coords(self):
        """Test parsing negative coordinates."""
        memory = {'location': 'Latitude, Longitude: -33.8688, 151.2093'}
        coords = parse_location(memory)

        assert coords == (-33.8688, 151.2093)

    def test_parse_location_no_location(self):
        """Test parsing when location field is missing."""
        memory = {}
        coords = parse_location(memory)

        assert coords is None

    def test_parse_location_empty_string(self):
        """Test parsing empty location string."""
        memory = {'location': ''}
        coords = parse_location(memory)

        assert coords is None

    def test_parse_location_invalid_format(self):
        """Test parsing invalid location format."""
        invalid_locations = [
            {'location': 'Invalid format'},
            {'location': 'Latitude: 42.438072'},
            {'location': '42.438072, -82.91975'},  # Missing prefix
            {'location': 'Latitude, Longitude: invalid, coords'},
        ]

        for memory in invalid_locations:
            coords = parse_location(memory)
            assert coords is None

    def test_parse_location_with_extra_whitespace(self):
        """Test parsing with extra whitespace."""
        memory = {'location': 'Latitude, Longitude:   42.438072  ,  -82.91975  '}
        coords = parse_location(memory)

        assert coords == (42.438072, -82.91975)


class TestAddGpsMetadata:
    """Test adding GPS metadata to files."""

    def test_add_gps_no_exiftool(self, tmp_path):
        """Test that function returns early when exiftool is not available."""
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'location': 'Latitude, Longitude: 42.438072, -82.91975'}

        # Should return without error when exiftool not available
        add_gps_metadata(test_file, memory, has_exiftool=False)

    def test_add_gps_no_coordinates(self, tmp_path):
        """Test that function returns when no coordinates are available."""
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'location': ''}

        # Should return without error
        add_gps_metadata(test_file, memory, has_exiftool=True)

    @patch('subprocess.run')
    @patch('snap_config.get_exiftool_path')
    def test_add_gps_to_jpg(self, mock_get_path, mock_run, tmp_path):
        """Test adding GPS metadata to JPG file."""
        mock_get_path.return_value = 'exiftool'
        mock_run.return_value = Mock(returncode=0)

        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'location': 'Latitude, Longitude: 42.438072, -82.91975'}
        add_gps_metadata(test_file, memory, has_exiftool=True)

        # Verify exiftool was called with correct parameters
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'exiftool'
        assert '-GPSLatitude=42.438072' in call_args
        assert '-GPSLatitudeRef=N' in call_args
        assert '-GPSLongitude=82.91975' in call_args
        assert '-GPSLongitudeRef=W' in call_args
        assert '-overwrite_original' in call_args

    @patch('subprocess.run')
    @patch('snap_config.get_exiftool_path')
    def test_add_gps_to_mp4(self, mock_get_path, mock_run, tmp_path):
        """Test adding GPS metadata to MP4 video file."""
        mock_get_path.return_value = 'exiftool'
        mock_run.return_value = Mock(returncode=0)

        test_file = tmp_path / "test.mp4"
        test_file.write_text("test content")

        memory = {'location': 'Latitude, Longitude: 40.7128, -74.0060'}
        add_gps_metadata(test_file, memory, has_exiftool=True)

        mock_run.assert_called_once()

    @patch('snap_config.get_exiftool_path')
    def test_add_gps_skip_png_overlay(self, mock_get_path, tmp_path):
        """Test that PNG overlays are skipped."""
        mock_get_path.return_value = 'exiftool'

        test_file = tmp_path / "overlay.png"
        test_file.write_text("test content")

        memory = {'location': 'Latitude, Longitude: 42.438072, -82.91975'}

        # Should not call exiftool for PNG files
        with patch('subprocess.run') as mock_run:
            add_gps_metadata(test_file, memory, has_exiftool=True)
            mock_run.assert_not_called()

    @patch('subprocess.run')
    @patch('snap_config.get_exiftool_path')
    def test_add_gps_southern_hemisphere(self, mock_get_path, mock_run, tmp_path):
        """Test GPS coordinates in southern hemisphere."""
        mock_get_path.return_value = 'exiftool'
        mock_run.return_value = Mock(returncode=0)

        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'location': 'Latitude, Longitude: -33.8688, 151.2093'}
        add_gps_metadata(test_file, memory, has_exiftool=True)

        call_args = mock_run.call_args[0][0]
        assert '-GPSLatitude=33.8688' in call_args
        assert '-GPSLatitudeRef=S' in call_args
        assert '-GPSLongitude=151.2093' in call_args
        assert '-GPSLongitudeRef=E' in call_args

    @patch('subprocess.run')
    @patch('snap_config.get_exiftool_path')
    def test_add_gps_handles_timeout(self, mock_get_path, mock_run, tmp_path):
        """Test that timeouts are handled gracefully."""
        mock_get_path.return_value = 'exiftool'
        mock_run.side_effect = Exception("Timeout")

        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        memory = {'location': 'Latitude, Longitude: 42.438072, -82.91975'}

        # Should not raise exception
        add_gps_metadata(test_file, memory, has_exiftool=True)


class TestCopyMetadataWithExiftool:
    """Test copying metadata between files."""

    @patch('subprocess.run')
    @patch('snap_config.get_exiftool_path')
    def test_copy_metadata_success(self, mock_get_path, mock_run, tmp_path):
        """Test successful metadata copy."""
        mock_get_path.return_value = 'exiftool'
        mock_run.return_value = Mock(returncode=0)

        source_file = tmp_path / "source.jpg"
        dest_file = tmp_path / "dest.jpg"
        source_file.write_text("source")
        dest_file.write_text("dest")

        copy_metadata_with_exiftool(source_file, dest_file, has_exiftool=True)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'exiftool'
        assert '-TagsFromFile' in call_args
        assert str(source_file) in call_args
        assert '-all:all' in call_args
        assert '-overwrite_original' in call_args

    def test_copy_metadata_no_exiftool(self, tmp_path):
        """Test that function returns early when exiftool not available."""
        source_file = tmp_path / "source.jpg"
        dest_file = tmp_path / "dest.jpg"
        source_file.write_text("source")
        dest_file.write_text("dest")

        # Should not raise error
        copy_metadata_with_exiftool(source_file, dest_file, has_exiftool=False)

    @patch('subprocess.run')
    @patch('snap_config.get_exiftool_path')
    def test_copy_metadata_handles_error(self, mock_get_path, mock_run, tmp_path):
        """Test that errors are handled gracefully."""
        mock_get_path.return_value = 'exiftool'
        mock_run.side_effect = Exception("Error")

        source_file = tmp_path / "source.jpg"
        dest_file = tmp_path / "dest.jpg"
        source_file.write_text("source")
        dest_file.write_text("dest")

        # Should not raise exception
        copy_metadata_with_exiftool(source_file, dest_file, has_exiftool=True)


class TestUpdateExistingFileMetadata:
    """Test updating metadata on existing files."""

    def test_update_metadata_for_images(self, tmp_path):
        """Test updating metadata for image files."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True)

        # Create test file
        test_file = images_dir / "2023-01-15_143000_Image_abc12345.jpg"
        test_file.write_text("test")

        memory = {
            'date': '2023-01-15 14:30:00 UTC',
            'location': 'Latitude, Longitude: 42.438072, -82.91975'
        }

        update_existing_file_metadata(
            output_dir, memory, 'abc12345xyz',
            has_exiftool=False, has_pywin32=False
        )

        # Verify timestamp was updated
        stat = os.stat(test_file)
        expected_dt = datetime.strptime('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
        expected_timestamp = expected_dt.timestamp()
        assert abs(stat.st_mtime - expected_timestamp) < 1

    def test_update_metadata_for_videos(self, tmp_path):
        """Test updating metadata for video files."""
        output_dir = tmp_path / "memories"
        videos_dir = output_dir / "videos"
        videos_dir.mkdir(parents=True)

        test_file = videos_dir / "2023-01-15_143000_Video_abc12345.mp4"
        test_file.write_text("test")

        memory = {'date': '2023-01-15 14:30:00 UTC'}

        update_existing_file_metadata(
            output_dir, memory, 'abc12345xyz',
            has_exiftool=False, has_pywin32=False
        )

        stat = os.stat(test_file)
        expected_dt = datetime.strptime('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
        expected_timestamp = expected_dt.timestamp()
        assert abs(stat.st_mtime - expected_timestamp) < 1

    def test_update_metadata_for_overlays(self, tmp_path):
        """Test updating metadata for overlay files."""
        output_dir = tmp_path / "memories"
        overlays_dir = output_dir / "overlays"
        overlays_dir.mkdir(parents=True)

        test_file = overlays_dir / "2023-01-15_143000_Image_abc12345_overlay.png"
        test_file.write_text("test")

        memory = {'date': '2023-01-15 14:30:00 UTC'}

        update_existing_file_metadata(
            output_dir, memory, 'abc12345xyz',
            has_exiftool=False, has_pywin32=False
        )

        stat = os.stat(test_file)
        expected_dt = datetime.strptime('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
        expected_timestamp = expected_dt.timestamp()
        assert abs(stat.st_mtime - expected_timestamp) < 1

    def test_update_metadata_no_matching_files(self, tmp_path):
        """Test when no matching files are found."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True)

        memory = {'date': '2023-01-15 14:30:00 UTC'}

        # Should not raise error when no files found
        update_existing_file_metadata(
            output_dir, memory, 'nonexistent',
            has_exiftool=False, has_pywin32=False
        )

    def test_update_metadata_handles_error(self, tmp_path):
        """Test that errors on individual files don't crash the function."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True)

        test_file = images_dir / "2023-01-15_143000_Image_abc12345.jpg"
        test_file.write_text("test")

        # Make file read-only to cause error
        test_file.chmod(0o444)

        memory = {'date': 'invalid date format'}  # This will cause an error

        # Should not raise exception
        try:
            update_existing_file_metadata(
                output_dir, memory, 'abc12345xyz',
                has_exiftool=False, has_pywin32=False
            )
        finally:
            # Restore permissions
            test_file.chmod(0o644)
