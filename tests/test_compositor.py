"""
Unit tests for compositor module.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import Mock, patch, MagicMock, call

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from compositor import (
    find_overlay_pairs,
    composite_image,
    composite_video,
    get_video_dimensions,
    _get_simple_dimensions
)


class TestFindOverlayPairs:
    """Test finding overlay pairs."""

    def test_find_pairs_basic(self, tmp_path):
        """Test finding basic overlay pairs."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        videos_dir = output_dir / "videos"
        overlays_dir = output_dir / "overlays"

        images_dir.mkdir(parents=True)
        videos_dir.mkdir(parents=True)
        overlays_dir.mkdir(parents=True)

        # Create test files
        (images_dir / "2023-01-15_143000_Image_abc12345.jpg").write_text("image")
        (overlays_dir / "2023-01-15_143000_Image_abc12345_overlay.png").write_text("overlay")
        (videos_dir / "2023-01-15_143000_Video_xyz78901.mp4").write_text("video")
        (overlays_dir / "2023-01-15_143000_Video_xyz78901_overlay.png").write_text("overlay")

        pairs = find_overlay_pairs(output_dir, use_cache=False)

        assert len(pairs) == 2

        # Check image pair
        image_pair = [p for p in pairs if p['media_type'] == 'image'][0]
        assert image_pair['sid'] == 'abc12345'
        assert image_pair['base_file'].name == "2023-01-15_143000_Image_abc12345.jpg"
        assert image_pair['overlay_file'].name == "2023-01-15_143000_Image_abc12345_overlay.png"

        # Check video pair
        video_pair = [p for p in pairs if p['media_type'] == 'video'][0]
        assert video_pair['sid'] == 'xyz78901'

    def test_find_pairs_no_overlays_dir(self, tmp_path):
        """Test when overlays directory doesn't exist."""
        output_dir = tmp_path / "memories"
        output_dir.mkdir()

        pairs = find_overlay_pairs(output_dir, use_cache=False)

        assert len(pairs) == 0

    def test_find_pairs_no_matching_base(self, tmp_path):
        """Test overlay without matching base file."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        overlays_dir = output_dir / "overlays"

        images_dir.mkdir(parents=True)
        overlays_dir.mkdir(parents=True)

        # Create overlay without base
        (overlays_dir / "2023-01-15_143000_Image_abc12345_overlay.png").write_text("overlay")

        pairs = find_overlay_pairs(output_dir, use_cache=False)

        assert len(pairs) == 0

    def test_find_pairs_timezone_agnostic(self, tmp_path):
        """Test that pairing works across timezone conversions."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        overlays_dir = output_dir / "overlays"

        images_dir.mkdir(parents=True)
        overlays_dir.mkdir(parents=True)

        # Base file with local timezone
        (images_dir / "2023-01-15_093000_Image_abc12345.jpg").write_text("image")
        # Overlay with UTC timezone
        (overlays_dir / "2023-01-15_143000_Image_abc12345_overlay.png").write_text("overlay")

        pairs = find_overlay_pairs(output_dir, use_cache=False)

        # Should find pair despite different timestamps (same SID)
        assert len(pairs) == 1
        assert pairs[0]['sid'] == 'abc12345'

    def test_find_pairs_cache_save_and_load(self, tmp_path):
        """Test that cache is saved and loaded correctly."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        overlays_dir = output_dir / "overlays"
        cache_file = str(tmp_path / "test_cache.json")

        images_dir.mkdir(parents=True)
        overlays_dir.mkdir(parents=True)

        (images_dir / "2023-01-15_143000_Image_abc12345.jpg").write_text("image")
        (overlays_dir / "2023-01-15_143000_Image_abc12345_overlay.png").write_text("overlay")

        # First call - should build and save cache
        pairs1 = find_overlay_pairs(output_dir, pairs_cache_file=cache_file, use_cache=False)
        assert len(pairs1) == 1
        assert Path(cache_file).exists()

        # Second call - should load from cache
        pairs2 = find_overlay_pairs(output_dir, pairs_cache_file=cache_file, use_cache=True)
        assert len(pairs2) == 1
        assert pairs2[0]['sid'] == pairs1[0]['sid']

    def test_find_pairs_cache_corrupted(self, tmp_path, capsys):
        """Test handling of corrupted cache file."""
        output_dir = tmp_path / "memories"
        images_dir = output_dir / "images"
        overlays_dir = output_dir / "overlays"
        cache_file = str(tmp_path / "corrupted_cache.json")

        images_dir.mkdir(parents=True)
        overlays_dir.mkdir(parents=True)

        (images_dir / "2023-01-15_143000_Image_abc12345.jpg").write_text("image")
        (overlays_dir / "2023-01-15_143000_Image_abc12345_overlay.png").write_text("overlay")

        # Create corrupted cache
        Path(cache_file).write_text("{ invalid json")

        # Should rebuild cache when corrupted
        pairs = find_overlay_pairs(output_dir, pairs_cache_file=cache_file, use_cache=True)
        assert len(pairs) == 1

        captured = capsys.readouterr()
        assert "Cache load failed" in captured.out or "rebuilding" in captured.out

    def test_find_pairs_invalid_filename_format(self, tmp_path):
        """Test that invalid filenames are skipped."""
        output_dir = tmp_path / "memories"
        overlays_dir = output_dir / "overlays"
        overlays_dir.mkdir(parents=True)

        # Create files with invalid formats
        (overlays_dir / "invalid_overlay.png").write_text("overlay")
        (overlays_dir / "2023-01-15_overlay.png").write_text("overlay")
        (overlays_dir / "no_type_abc12345_overlay.png").write_text("overlay")

        pairs = find_overlay_pairs(output_dir, use_cache=False)

        assert len(pairs) == 0


class TestCompositeImage:
    """Test image compositing."""

    def test_composite_image_basic(self, tmp_path):
        """Test basic image compositing."""
        pytest.importorskip("PIL")
        from PIL import Image

        output_dir = tmp_path / "memories"
        composited_dir = output_dir / "composited" / "images"
        composited_dir.mkdir(parents=True)

        # Create base image (red 100x100)
        base_file = tmp_path / "base.jpg"
        base_img = Image.new('RGB', (100, 100), color='red')
        base_img.save(base_file)

        # Create overlay (semi-transparent blue 100x100)
        overlay_file = tmp_path / "overlay.png"
        overlay_img = Image.new('RGBA', (100, 100), color=(0, 0, 255, 128))
        overlay_img.save(overlay_file)

        success, message = composite_image(base_file, overlay_file, output_dir, has_exiftool=False)

        assert success is True
        assert message == "Success"

        # Check output file exists
        output_file = composited_dir / "base_composited.jpg"
        assert output_file.exists()

        # Verify the output is valid image
        result_img = Image.open(output_file)
        assert result_img.size == (100, 100)

    def test_composite_image_different_sizes(self, tmp_path):
        """Test compositing images of different sizes."""
        pytest.importorskip("PIL")
        from PIL import Image

        output_dir = tmp_path / "memories"
        composited_dir = output_dir / "composited" / "images"
        composited_dir.mkdir(parents=True)

        # Create base image 200x200
        base_file = tmp_path / "base.jpg"
        base_img = Image.new('RGB', (200, 200), color='red')
        base_img.save(base_file)

        # Create overlay 100x100 (will be resized)
        overlay_file = tmp_path / "overlay.png"
        overlay_img = Image.new('RGBA', (100, 100), color=(0, 0, 255, 128))
        overlay_img.save(overlay_file)

        success, message = composite_image(base_file, overlay_file, output_dir, has_exiftool=False)

        assert success is True

        # Verify output has base image dimensions
        output_file = composited_dir / "base_composited.jpg"
        result_img = Image.open(output_file)
        assert result_img.size == (200, 200)

    def test_composite_image_missing_pillow(self, tmp_path):
        """Test error when PIL is not available."""
        base_file = tmp_path / "base.jpg"
        overlay_file = tmp_path / "overlay.png"
        base_file.write_text("fake image")
        overlay_file.write_text("fake overlay")

        with patch.dict('sys.modules', {'PIL': None}):
            success, message = composite_image(base_file, overlay_file, tmp_path, has_exiftool=False)

            assert success is False
            assert "Error" in message

    def test_composite_image_preserves_timestamps(self, tmp_path):
        """Test that output file has same timestamp as base."""
        pytest.importorskip("PIL")
        from PIL import Image
        import os
        import time

        output_dir = tmp_path / "memories"
        composited_dir = output_dir / "composited" / "images"
        composited_dir.mkdir(parents=True)

        # Create base image
        base_file = tmp_path / "base.jpg"
        base_img = Image.new('RGB', (100, 100), color='red')
        base_img.save(base_file)

        # Set specific timestamp
        old_time = time.time() - 86400  # 1 day ago
        os.utime(base_file, (old_time, old_time))

        # Create overlay
        overlay_file = tmp_path / "overlay.png"
        overlay_img = Image.new('RGBA', (100, 100), color=(0, 0, 255, 128))
        overlay_img.save(overlay_file)

        composite_image(base_file, overlay_file, output_dir, has_exiftool=False)

        # Check timestamp was preserved
        output_file = composited_dir / "base_composited.jpg"
        output_stat = os.stat(output_file)
        base_stat = os.stat(base_file)

        assert abs(output_stat.st_mtime - base_stat.st_mtime) < 1


class TestCompositeVideo:
    """Test video compositing."""

    @patch('subprocess.run')
    def test_composite_video_basic(self, mock_run, tmp_path):
        """Test basic video compositing."""
        # Mock successful ffmpeg execution
        mock_run.return_value = Mock(returncode=0, stderr="")

        output_dir = tmp_path / "memories"
        composited_dir = output_dir / "composited" / "videos"
        composited_dir.mkdir(parents=True)

        base_file = tmp_path / "base.mp4"
        overlay_file = tmp_path / "overlay.png"
        base_file.write_text("fake video")
        overlay_file.write_text("fake overlay")

        # Mock video dimensions and ensure output file is created
        with patch('compositor.get_video_dimensions', return_value=(1920, 1080)):
            # Create the output file that ffmpeg would create
            def create_output_file(*args, **kwargs):
                output_path = composited_dir / "base_composited.mp4"
                output_path.write_text("composited video")
                return Mock(returncode=0, stderr="")

            mock_run.side_effect = create_output_file

            success, message = composite_video(base_file, overlay_file, output_dir, has_exiftool=False)

        assert success is True
        assert message == "Success"

        # Verify ffmpeg was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'ffmpeg'
        assert '-i' in call_args

    @patch('subprocess.run')
    def test_composite_video_with_overlay_scaling(self, mock_run, tmp_path):
        """Test that overlay is scaled to match video dimensions."""
        output_dir = tmp_path / "memories"
        composited_dir = output_dir / "composited" / "videos"
        composited_dir.mkdir(parents=True)

        base_file = tmp_path / "base.mp4"
        overlay_file = tmp_path / "overlay.png"
        base_file.write_text("fake video")
        overlay_file.write_text("fake overlay")

        # Mock ffmpeg to create output file
        def create_output_file(*args, **kwargs):
            output_path = composited_dir / "base_composited.mp4"
            output_path.write_text("composited video")
            return Mock(returncode=0, stderr="")

        mock_run.side_effect = create_output_file

        with patch('compositor.get_video_dimensions', return_value=(1280, 720)):
            composite_video(base_file, overlay_file, output_dir, has_exiftool=False)

        # Check that filter_complex includes correct dimensions
        call_args = mock_run.call_args[0][0]
        filter_idx = call_args.index('-filter_complex')
        filter_value = call_args[filter_idx + 1]
        assert '1280:720' in filter_value

    @patch('subprocess.run')
    def test_composite_video_ffmpeg_error(self, mock_run, tmp_path):
        """Test handling FFmpeg errors."""
        mock_run.return_value = Mock(returncode=1, stderr="FFmpeg error message")

        output_dir = tmp_path / "memories"
        composited_dir = output_dir / "composited" / "videos"
        composited_dir.mkdir(parents=True)

        base_file = tmp_path / "base.mp4"
        overlay_file = tmp_path / "overlay.png"
        base_file.write_text("fake video")
        overlay_file.write_text("fake overlay")

        with patch('compositor.get_video_dimensions', return_value=(1920, 1080)):
            success, message = composite_video(base_file, overlay_file, output_dir, has_exiftool=False)

        assert success is False
        assert "FFmpeg error" in message

    @patch('subprocess.run')
    def test_composite_video_timeout(self, mock_run, tmp_path):
        """Test handling of video processing timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('ffmpeg', 300)

        output_dir = tmp_path / "memories"
        composited_dir = output_dir / "composited" / "videos"
        composited_dir.mkdir(parents=True)

        base_file = tmp_path / "base.mp4"
        overlay_file = tmp_path / "overlay.png"
        base_file.write_text("fake video")
        overlay_file.write_text("fake overlay")

        with patch('compositor.get_video_dimensions', return_value=(1920, 1080)):
            success, message = composite_video(base_file, overlay_file, output_dir, has_exiftool=False)

        assert success is False
        assert "Timeout" in message


class TestGetVideoDimensions:
    """Test getting video dimensions."""

    @patch('subprocess.run')
    def test_get_dimensions_with_rotation(self, mock_run):
        """Test getting dimensions accounting for rotation."""
        # Mock ffprobe output with rotation
        mock_output = json.dumps({
            'streams': [{
                'width': 1080,
                'height': 1920,
                'side_data_list': [{'rotation': -90}]
            }]
        })
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)

        video_file = Path("test.mp4")
        width, height = get_video_dimensions(video_file)

        # Dimensions should be swapped due to 90-degree rotation
        assert width == 1920
        assert height == 1080

    @patch('subprocess.run')
    def test_get_dimensions_no_rotation(self, mock_run):
        """Test getting dimensions without rotation."""
        mock_output = json.dumps({
            'streams': [{
                'width': 1920,
                'height': 1080
            }]
        })
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)

        video_file = Path("test.mp4")
        width, height = get_video_dimensions(video_file)

        assert width == 1920
        assert height == 1080

    @patch('subprocess.run')
    def test_get_dimensions_270_rotation(self, mock_run):
        """Test dimensions with 270-degree rotation."""
        mock_output = json.dumps({
            'streams': [{
                'width': 1080,
                'height': 1920,
                'side_data_list': [{'rotation': -270}]
            }]
        })
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)

        video_file = Path("test.mp4")
        width, height = get_video_dimensions(video_file)

        # Should swap for 270 degrees
        assert width == 1920
        assert height == 1080

    @patch('subprocess.run')
    def test_get_dimensions_fallback(self, mock_run):
        """Test fallback when ffprobe fails."""
        mock_run.return_value = Mock(returncode=1, stdout="")

        video_file = Path("test.mp4")

        with patch('compositor._get_simple_dimensions', return_value=(1920, 1080)) as mock_simple:
            width, height = get_video_dimensions(video_file)

        mock_simple.assert_called_once()
        assert width == 1920
        assert height == 1080

    @patch('subprocess.run')
    def test_get_simple_dimensions(self, mock_run):
        """Test simple dimension query."""
        mock_run.return_value = Mock(returncode=0, stdout="1920x1080\n")

        video_file = Path("test.mp4")
        width, height = _get_simple_dimensions(video_file)

        assert width == 1920
        assert height == 1080

    @patch('subprocess.run')
    def test_get_simple_dimensions_error_fallback(self, mock_run):
        """Test fallback to default dimensions on error."""
        mock_run.return_value = Mock(returncode=1, stdout="")

        video_file = Path("test.mp4")
        width, height = _get_simple_dimensions(video_file)

        # Should return default fallback
        assert width == 1920
        assert height == 1080
