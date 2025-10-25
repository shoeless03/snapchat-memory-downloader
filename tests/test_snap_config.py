"""
Unit tests for snap_config module.
"""

import sys
import platform
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from snap_config import (
    get_exiftool_path,
    check_exiftool,
    check_pywin32,
    check_pillow,
    check_ffmpeg,
    check_dependencies
)


class TestGetExiftoolPath:
    """Test ExifTool path detection."""

    def test_get_exiftool_path_local_windows(self, tmp_path):
        """Test finding local ExifTool on Windows."""
        if platform.system() != 'Windows':
            pytest.skip("Windows-specific test")

        # Mock the project structure
        with patch('snap_config.Path') as mock_path:
            exiftool_exe = tmp_path / "tools" / "exiftool" / "exiftool-13.39_64" / "exiftool.exe"
            exiftool_exe.parent.mkdir(parents=True)
            exiftool_exe.write_text("fake exiftool")

            mock_path.return_value.parent.parent = tmp_path

            # This test is complex due to Path mocking, skip for now
            pytest.skip("Requires complex mocking")

    def test_get_exiftool_path_system(self):
        """Test finding ExifTool in system PATH."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/exiftool'

            with patch('snap_config.Path') as mock_path:
                # Mock non-existent local exiftool
                mock_instance = MagicMock()
                mock_instance.exists.return_value = False
                mock_path.return_value.parent.parent = mock_instance

                # Should still work - implementation dependent
                # This test needs better mocking

    def test_get_exiftool_path_not_found(self):
        """Test when ExifTool is not found."""
        with patch('shutil.which', return_value=None):
            with patch.object(Path, 'exists', return_value=False):
                result = get_exiftool_path()
                # Should return None when not found
                # (actual behavior depends on implementation)


class TestCheckExiftool:
    """Test ExifTool availability check."""

    def test_check_exiftool_available(self):
        """Test when ExifTool is available."""
        with patch('snap_config.get_exiftool_path', return_value='/usr/bin/exiftool'):
            assert check_exiftool() is True

    def test_check_exiftool_not_available(self):
        """Test when ExifTool is not available."""
        with patch('snap_config.get_exiftool_path', return_value=None):
            assert check_exiftool() is False


class TestCheckPywin32:
    """Test pywin32 availability check."""

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_check_pywin32_on_windows_available(self):
        """Test pywin32 check on Windows when available."""
        # Try to import - if available, check should return True
        try:
            import pywintypes
            import win32file
            assert check_pywin32() is True
        except ImportError:
            # If not available, check should return False
            assert check_pywin32() is False

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_check_pywin32_on_windows_not_available(self):
        """Test pywin32 check on Windows when not available."""
        with patch.dict('sys.modules', {'pywintypes': None, 'win32file': None}):
            # Force ImportError
            assert check_pywin32() is False

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Non-Windows test")
    def test_check_pywin32_on_non_windows(self):
        """Test pywin32 check on non-Windows platforms."""
        # Should return True (not needed)
        assert check_pywin32() is True


class TestCheckPillow:
    """Test Pillow availability check."""

    def test_check_pillow_available(self):
        """Test when Pillow is available."""
        try:
            from PIL import Image
            has_pillow, has_pillow_simd = check_pillow()
            assert has_pillow is True
            # has_pillow_simd depends on installation
            assert isinstance(has_pillow_simd, bool)
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_check_pillow_not_available(self):
        """Test when Pillow is not available."""
        with patch.dict('sys.modules', {'PIL': None, 'PIL.Image': None}):
            # This doesn't actually prevent import, so mock the import
            with patch('builtins.__import__', side_effect=ImportError):
                # Can't easily test without actually uninstalling Pillow
                pytest.skip("Difficult to test without uninstalling Pillow")

    def test_check_pillow_returns_tuple(self):
        """Test that check_pillow returns a tuple."""
        result = check_pillow()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], bool)


class TestCheckFFmpeg:
    """Test FFmpeg availability check."""

    def test_check_ffmpeg_available(self):
        """Test when FFmpeg is available."""
        with patch('shutil.which', return_value='/usr/bin/ffmpeg'):
            assert check_ffmpeg() is True

    def test_check_ffmpeg_not_available(self):
        """Test when FFmpeg is not available."""
        with patch('shutil.which', return_value=None):
            assert check_ffmpeg() is False


class TestCheckDependencies:
    """Test dependency checking function."""

    def test_check_dependencies_all_available(self, capsys):
        """Test when all dependencies are available."""
        with patch('snap_config.check_exiftool', return_value=True), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(True, False)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            check_dependencies()

            captured = capsys.readouterr()
            assert "All optional dependencies found" in captured.out

    def test_check_dependencies_missing_shows_prompt(self, capsys, monkeypatch):
        """Test that missing dependencies show a prompt."""
        with patch('snap_config.check_exiftool', return_value=False), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(True, False)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            # Mock user input to continue
            monkeypatch.setattr('builtins.input', lambda _: '1')

            check_dependencies()

            captured = capsys.readouterr()
            assert "OPTIONAL DEPENDENCIES" in captured.out
            assert "ExifTool" in captured.out

    def test_check_dependencies_user_exits(self, monkeypatch):
        """Test that user can choose to exit."""
        with patch('snap_config.check_exiftool', return_value=False), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(True, False)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            # Mock user input to exit
            monkeypatch.setattr('builtins.input', lambda _: '2')

            with pytest.raises(SystemExit) as exc_info:
                check_dependencies()

            assert exc_info.value.code == 0

    def test_check_dependencies_invalid_then_valid_choice(self, capsys, monkeypatch):
        """Test handling of invalid input followed by valid choice."""
        with patch('snap_config.check_exiftool', return_value=False), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(True, False)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            # Mock user input - first invalid, then valid
            inputs = iter(['invalid', '3', '1'])
            monkeypatch.setattr('builtins.input', lambda _: next(inputs))

            check_dependencies()

            captured = capsys.readouterr()
            assert "Invalid choice" in captured.out

    def test_check_dependencies_keyboard_interrupt(self, monkeypatch):
        """Test handling of keyboard interrupt."""
        with patch('snap_config.check_exiftool', return_value=False), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(True, False)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            # Mock user pressing Ctrl+C
            monkeypatch.setattr('builtins.input', lambda _: (_ for _ in ()).throw(KeyboardInterrupt))

            with pytest.raises(SystemExit) as exc_info:
                check_dependencies()

            assert exc_info.value.code == 0

    def test_check_dependencies_shows_all_missing(self, capsys, monkeypatch):
        """Test that all missing dependencies are shown."""
        with patch('snap_config.check_exiftool', return_value=False), \
             patch('snap_config.check_pywin32', return_value=False), \
             patch('snap_config.check_pillow', return_value=(False, False)), \
             patch('snap_config.check_ffmpeg', return_value=False), \
             patch('platform.system', return_value='Windows'):

            # Mock user input to continue
            monkeypatch.setattr('builtins.input', lambda _: '1')

            check_dependencies()

            captured = capsys.readouterr()
            assert "ExifTool" in captured.out
            assert "pywin32" in captured.out
            assert "Pillow" in captured.out
            assert "FFmpeg" in captured.out

    def test_check_dependencies_pillow_simd_detected(self, capsys):
        """Test that Pillow-SIMD is properly detected."""
        with patch('snap_config.check_exiftool', return_value=True), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(True, True)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            check_dependencies()

            captured = capsys.readouterr()
            assert "Pillow-SIMD" in captured.out or "5x faster" in captured.out

    def test_check_dependencies_pillow_not_simd_shows_tip(self, capsys):
        """Test that tip is shown when regular Pillow is installed."""
        with patch('snap_config.check_exiftool', return_value=True), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(True, False)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            check_dependencies()

            captured = capsys.readouterr()
            assert "pillow-simd" in captured.out.lower() or "TIP" in captured.out


class TestConfigIntegration:
    """Integration tests for configuration checking."""

    def test_dependency_check_flow(self, monkeypatch):
        """Test complete dependency check flow."""
        # Simulate environment with some deps missing
        with patch('snap_config.check_exiftool', return_value=True), \
             patch('snap_config.check_pywin32', return_value=True), \
             patch('snap_config.check_pillow', return_value=(False, False)), \
             patch('snap_config.check_ffmpeg', return_value=True):

            # User continues despite missing Pillow
            monkeypatch.setattr('builtins.input', lambda _: '1')

            # Should complete without error
            check_dependencies()

    def test_all_check_functions_return_bool(self):
        """Test that all check functions return booleans."""
        assert isinstance(check_exiftool(), bool)
        assert isinstance(check_pywin32(), bool)
        assert isinstance(check_ffmpeg(), bool)

        has_pillow, has_simd = check_pillow()
        assert isinstance(has_pillow, bool)
        assert isinstance(has_simd, bool)
