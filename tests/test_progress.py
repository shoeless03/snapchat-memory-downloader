"""
Unit tests for progress tracker module.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from progress import ProgressTracker


class TestProgressTrackerInit:
    """Test ProgressTracker initialization."""

    def test_init_new_file(self, tmp_path):
        """Test initialization with new progress file."""
        progress_file = str(tmp_path / "progress.json")
        tracker = ProgressTracker(progress_file)

        assert tracker.progress_file == progress_file
        assert tracker.progress['downloaded'] == {}
        assert tracker.progress['failed'] == {}
        assert 'composited' in tracker.progress
        assert 'failed_composites' in tracker.progress

    def test_init_existing_file(self, tmp_path):
        """Test initialization with existing progress file."""
        progress_file = tmp_path / "progress.json"
        existing_data = {
            'downloaded': {'sid123': {'date': '2023-01-15 14:30:00 UTC'}},
            'failed': {},
            'composited': {'images': {}, 'videos': {}},
            'failed_composites': {'images': {}, 'videos': {}}
        }
        progress_file.write_text(json.dumps(existing_data))

        tracker = ProgressTracker(str(progress_file))

        assert 'sid123' in tracker.progress['downloaded']

    def test_init_corrupted_file(self, tmp_path):
        """Test that corrupted progress file causes exit."""
        progress_file = tmp_path / "corrupted.json"
        progress_file.write_text("{ invalid json")

        with pytest.raises(SystemExit):
            ProgressTracker(str(progress_file))

    def test_init_invalid_structure(self, tmp_path):
        """Test that non-dict progress file causes exit."""
        progress_file = tmp_path / "invalid.json"
        progress_file.write_text("[]")  # Array instead of object

        with pytest.raises(SystemExit):
            ProgressTracker(str(progress_file))


class TestDownloadTracking:
    """Test download tracking functionality."""

    def test_is_downloaded_false(self, tmp_path):
        """Test checking if SID is not downloaded."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))
        assert tracker.is_downloaded('sid123') is False

    def test_mark_downloaded(self, tmp_path):
        """Test marking SID as downloaded."""
        progress_file = str(tmp_path / "progress.json")
        tracker = ProgressTracker(progress_file)

        memory = {
            'date': '2023-01-15 14:30:00 UTC',
            'media_type': 'Image'
        }
        tracker.mark_downloaded('sid123', memory)

        assert tracker.is_downloaded('sid123') is True
        assert tracker.progress['downloaded']['sid123']['date'] == '2023-01-15 14:30:00 UTC'
        assert tracker.progress['downloaded']['sid123']['media_type'] == 'Image'
        assert tracker.progress['downloaded']['sid123']['timezone_converted'] is False

    def test_mark_downloaded_removes_from_failed(self, tmp_path):
        """Test that marking as downloaded removes from failed list."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        # First mark as failed
        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image', 'download_url': 'http://test'}
        tracker.record_failure('sid123', memory, "Error")

        assert 'sid123' in tracker.progress['failed']

        # Then mark as downloaded
        tracker.mark_downloaded('sid123', memory)

        assert tracker.is_downloaded('sid123') is True
        assert 'sid123' not in tracker.progress['failed']

    def test_record_failure(self, tmp_path):
        """Test recording download failure."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory = {
            'date': '2023-01-15 14:30:00 UTC',
            'download_url': 'http://example.com/file'
        }
        tracker.record_failure('sid123', memory, "Network error")

        assert 'sid123' in tracker.progress['failed']
        assert tracker.progress['failed']['sid123']['count'] == 1
        assert len(tracker.progress['failed']['sid123']['errors']) == 1
        assert tracker.progress['failed']['sid123']['errors'][0]['error'] == "Network error"

    def test_record_failure_multiple_times(self, tmp_path):
        """Test recording multiple failures for same SID."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'download_url': 'http://test'}

        tracker.record_failure('sid123', memory, "Error 1")
        tracker.record_failure('sid123', memory, "Error 2")
        tracker.record_failure('sid123', memory, "Error 3")

        assert tracker.progress['failed']['sid123']['count'] == 3
        assert len(tracker.progress['failed']['sid123']['errors']) == 3

    def test_get_failure_count(self, tmp_path):
        """Test getting failure count."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        assert tracker.get_failure_count('sid123') == 0

        memory = {'date': '2023-01-15 14:30:00 UTC', 'download_url': 'http://test'}
        tracker.record_failure('sid123', memory, "Error")

        assert tracker.get_failure_count('sid123') == 1

    def test_record_failure_with_exception(self, tmp_path):
        """Test recording failure with exception object."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'download_url': 'http://test'}
        exception = ValueError("Test error")

        tracker.record_failure('sid123', memory, "Error message", exception)

        assert tracker.progress['failed']['sid123']['errors'][0]['error_type'] == 'ValueError'


class TestCompositeTracking:
    """Test composite tracking functionality."""

    def test_is_composited_false(self, tmp_path):
        """Test checking if SID is not composited."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))
        assert tracker.is_composited('sid123', 'image') is False

    def test_mark_composited_image(self, tmp_path):
        """Test marking image as composited."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        tracker.mark_composited('sid123', 'image', '/path/to/base.jpg', '/path/to/overlay.png')

        assert tracker.is_composited('sid123', 'image') is True
        assert tracker.progress['composited']['images']['sid123']['base_file'] == '/path/to/base.jpg'
        assert tracker.progress['composited']['images']['sid123']['overlay_file'] == '/path/to/overlay.png'

    def test_mark_composited_video(self, tmp_path):
        """Test marking video as composited."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        tracker.mark_composited('sid456', 'video', '/path/to/base.mp4', '/path/to/overlay.png')

        assert tracker.is_composited('sid456', 'video') is True
        assert tracker.progress['composited']['videos']['sid456']['base_file'] == '/path/to/base.mp4'

    def test_mark_composited_removes_from_failed(self, tmp_path):
        """Test that marking as composited removes from failed composites."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        # First mark as failed
        tracker.record_composite_failure('sid123', 'image', '/path/base.jpg', '/path/overlay.png', "Error")

        # Then mark as composited
        tracker.mark_composited('sid123', 'image', '/path/base.jpg', '/path/overlay.png')

        assert tracker.is_composited('sid123', 'image') is True
        assert 'sid123' not in tracker.progress.get('failed_composites', {}).get('images', {})

    def test_record_composite_failure(self, tmp_path):
        """Test recording composite failure."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        tracker.record_composite_failure('sid123', 'image', '/path/base.jpg', '/path/overlay.png', "PIL error")

        failed_dict = tracker.progress['failed_composites']['images']
        assert 'sid123' in failed_dict
        assert failed_dict['sid123']['count'] == 1
        assert failed_dict['sid123']['errors'][0]['error'] == "PIL error"

    def test_get_composite_failure_count(self, tmp_path):
        """Test getting composite failure count."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        assert tracker.get_composite_failure_count('sid123', 'image') == 0

        tracker.record_composite_failure('sid123', 'image', '/path/base.jpg', '/path/overlay.png', "Error")

        assert tracker.get_composite_failure_count('sid123', 'image') == 1

    def test_composite_tracking_separate_by_type(self, tmp_path):
        """Test that image and video composites are tracked separately."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        tracker.mark_composited('sid123', 'image', '/path/img.jpg', '/path/overlay.png')
        tracker.mark_composited('sid123', 'video', '/path/vid.mp4', '/path/overlay.png')

        assert tracker.is_composited('sid123', 'image') is True
        assert tracker.is_composited('sid123', 'video') is True


class TestTimezoneTracking:
    """Test timezone conversion tracking."""

    def test_is_timezone_converted_false(self, tmp_path):
        """Test checking if timezone not converted."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory)

        assert tracker.is_timezone_converted('sid123') is False

    def test_mark_timezone_converted(self, tmp_path):
        """Test marking timezone as converted."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory)
        tracker.mark_timezone_converted('sid123', '2023-01-15 09:30:00 EST')

        assert tracker.is_timezone_converted('sid123') is True
        assert tracker.progress['downloaded']['sid123']['local_date'] == '2023-01-15 09:30:00 EST'

    def test_get_utc_date(self, tmp_path):
        """Test getting UTC date."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory)

        assert tracker.get_utc_date('sid123') == '2023-01-15 14:30:00 UTC'
        assert tracker.get_utc_date('nonexistent') is None

    def test_get_local_date(self, tmp_path):
        """Test getting local date."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory)
        tracker.mark_timezone_converted('sid123', '2023-01-15 09:30:00 EST')

        assert tracker.get_local_date('sid123') == '2023-01-15 09:30:00 EST'
        assert tracker.get_local_date('nonexistent') is None


class TestVerifyDownloads:
    """Test download verification."""

    def test_verify_downloads_all_downloaded(self, tmp_path):
        """Test verification when all are downloaded."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memories = [
            {'sid': 'sid1', 'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'},
            {'sid': 'sid2', 'date': '2023-01-16 10:20:00 UTC', 'media_type': 'Video'},
        ]

        for mem in memories:
            tracker.mark_downloaded(mem['sid'], mem)

        results = tracker.verify_downloads(memories)

        assert results['total'] == 2
        assert results['downloaded'] == 2
        assert len(results['missing']) == 0
        assert len(results['failed']) == 0

    def test_verify_downloads_with_missing(self, tmp_path):
        """Test verification with missing downloads."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memories = [
            {'sid': 'sid1', 'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'},
            {'sid': 'sid2', 'date': '2023-01-16 10:20:00 UTC', 'media_type': 'Video'},
            {'sid': 'sid3', 'date': '2023-01-17 08:15:00 UTC', 'media_type': 'Image'},
        ]

        tracker.mark_downloaded('sid1', memories[0])

        results = tracker.verify_downloads(memories)

        assert results['total'] == 3
        assert results['downloaded'] == 1
        assert len(results['missing']) == 2
        assert results['missing'][0]['sid'] == 'sid2'
        assert results['missing'][1]['sid'] == 'sid3'

    def test_verify_downloads_with_failed(self, tmp_path):
        """Test verification with failed downloads."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memories = [
            {'sid': 'sid1', 'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image', 'download_url': 'http://test1'},
            {'sid': 'sid2', 'date': '2023-01-16 10:20:00 UTC', 'media_type': 'Video', 'download_url': 'http://test2'},
        ]

        tracker.mark_downloaded('sid1', memories[0])
        tracker.record_failure('sid2', memories[1], "Error")
        tracker.record_failure('sid2', memories[1], "Error 2")

        results = tracker.verify_downloads(memories)

        assert results['total'] == 2
        assert results['downloaded'] == 1
        assert len(results['failed']) == 1
        assert results['failed'][0]['sid'] == 'sid2'
        assert results['failed'][0]['attempts'] == 2


class TestSaveProgress:
    """Test progress file saving."""

    def test_save_progress_creates_file(self, tmp_path):
        """Test that save creates progress file."""
        progress_file = tmp_path / "progress.json"
        tracker = ProgressTracker(str(progress_file))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory)

        assert progress_file.exists()

        # Verify content
        with open(progress_file) as f:
            data = json.load(f)

        assert 'sid123' in data['downloaded']

    def test_save_progress_creates_backup(self, tmp_path):
        """Test that save creates backup of existing file."""
        progress_file = tmp_path / "progress.json"
        backup_file = tmp_path / "progress.json.backup"

        tracker = ProgressTracker(str(progress_file))

        # First save
        memory1 = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid1', memory1)

        # Second save (should create backup)
        memory2 = {'date': '2023-01-16 10:20:00 UTC', 'media_type': 'Video'}
        tracker.mark_downloaded('sid2', memory2)

        assert backup_file.exists()

    def test_save_progress_atomic_write(self, tmp_path):
        """Test that save uses atomic write (via temp file)."""
        progress_file = tmp_path / "progress.json"
        tracker = ProgressTracker(str(progress_file))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory)

        # Verify no temp file left behind
        temp_file = tmp_path / "progress.json.tmp"
        assert not temp_file.exists()

        # Verify main file exists
        assert progress_file.exists()

    def test_save_progress_valid_json(self, tmp_path):
        """Test that saved file is valid JSON."""
        progress_file = tmp_path / "progress.json"
        tracker = ProgressTracker(str(progress_file))

        memory = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory)

        # Should be able to load without error
        with open(progress_file) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert 'downloaded' in data


class TestProgressTrackerEdgeCases:
    """Test edge cases and error handling."""

    def test_mark_downloaded_updates_existing(self, tmp_path):
        """Test that marking as downloaded updates existing entry."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        memory1 = {'date': '2023-01-15 14:30:00 UTC', 'media_type': 'Image'}
        tracker.mark_downloaded('sid123', memory1)

        memory2 = {'date': '2023-01-15 15:00:00 UTC', 'media_type': 'Video'}
        tracker.mark_downloaded('sid123', memory2)

        # Should have updated date
        assert tracker.progress['downloaded']['sid123']['date'] == '2023-01-15 15:00:00 UTC'
        assert tracker.progress['downloaded']['sid123']['media_type'] == 'Video'

    def test_is_composited_backwards_compatible(self, tmp_path):
        """Test that old progress files without composited key work."""
        progress_file = tmp_path / "old_progress.json"
        old_data = {
            'downloaded': {},
            'failed': {}
        }
        progress_file.write_text(json.dumps(old_data))

        tracker = ProgressTracker(str(progress_file))

        # Should not crash
        assert tracker.is_composited('sid123', 'image') is False

    def test_timezone_converted_nonexistent_sid(self, tmp_path):
        """Test timezone conversion check on nonexistent SID."""
        tracker = ProgressTracker(str(tmp_path / "progress.json"))

        assert tracker.is_timezone_converted('nonexistent') is False
