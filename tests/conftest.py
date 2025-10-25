"""
Pytest configuration and shared fixtures for Snapchat Memories Downloader tests.
"""

import sys
import json
from pathlib import Path
import pytest

# Add scripts directory to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# ===== File and Directory Fixtures =====

@pytest.fixture
def sample_html_file(tmp_path):
    """Create a sample HTML file with test memories data."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Memories History</title></head>
    <body>
        <h1>Your Memories</h1>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Media Type</th>
                    <th>Location</th>
                    <th>Download</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>2023-01-15 14:30:00 UTC</td>
                    <td>Image</td>
                    <td>Latitude, Longitude: 42.438072, -82.91975</td>
                    <td><a onclick="downloadMemories('https://example.com/download?sid=abc12345def67890', this, true)">Download</a></td>
                </tr>
                <tr>
                    <td>2023-01-16 10:20:00 UTC</td>
                    <td>Video</td>
                    <td></td>
                    <td><a onclick="downloadMemories('https://example.com/download?sid=xyz98765fed43210', this, false)">Download</a></td>
                </tr>
                <tr>
                    <td>2023-01-17 16:00:00 UTC</td>
                    <td>Image</td>
                    <td>Latitude, Longitude: 40.7128, -74.0060</td>
                    <td><a onclick="downloadMemories('https://example.com/download?sid=test123test456', this, true)">Download</a></td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """

    html_file = tmp_path / "memories_history.html"
    html_file.write_text(html_content, encoding='utf-8')
    return html_file


@pytest.fixture
def sample_memories():
    """Provide sample memory dictionaries for testing."""
    return [
        {
            'date': '2023-01-15 14:30:00 UTC',
            'media_type': 'Image',
            'location': 'Latitude, Longitude: 42.438072, -82.91975',
            'download_url': 'https://example.com/download?sid=abc12345def67890',
            'sid': 'abc12345def67890'
        },
        {
            'date': '2023-01-16 10:20:00 UTC',
            'media_type': 'Video',
            'location': '',
            'download_url': 'https://example.com/download?sid=xyz98765fed43210',
            'sid': 'xyz98765fed43210'
        },
        {
            'date': '2023-01-17 16:00:00 UTC',
            'media_type': 'Image',
            'location': 'Latitude, Longitude: 40.7128, -74.0060',
            'download_url': 'https://example.com/download?sid=test123test456',
            'sid': 'test123test456'
        }
    ]


@pytest.fixture
def output_directory_structure(tmp_path):
    """Create a standard output directory structure for testing."""
    output_dir = tmp_path / "memories"
    (output_dir / "images").mkdir(parents=True)
    (output_dir / "videos").mkdir(parents=True)
    (output_dir / "overlays").mkdir(parents=True)
    (output_dir / "composited" / "images").mkdir(parents=True)
    (output_dir / "composited" / "videos").mkdir(parents=True)

    return output_dir


@pytest.fixture
def progress_file(tmp_path):
    """Create a temporary progress file."""
    progress_file = tmp_path / "download_progress.json"
    initial_data = {
        'downloaded': {},
        'failed': {},
        'composited': {'images': {}, 'videos': {}},
        'failed_composites': {'images': {}, 'videos': {}}
    }
    progress_file.write_text(json.dumps(initial_data, indent=2))
    return progress_file


@pytest.fixture
def sample_image_pair(tmp_path):
    """Create sample image and overlay files for testing."""
    base_file = tmp_path / "2023-01-15_143000_Image_abc12345.jpg"
    overlay_file = tmp_path / "2023-01-15_143000_Image_abc12345_overlay.png"

    # Create minimal valid image files
    # These are fake but have correct magic bytes
    base_file.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)  # JPEG magic bytes
    overlay_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # PNG magic bytes

    return {'base': base_file, 'overlay': overlay_file, 'sid': 'abc12345'}


@pytest.fixture
def sample_video_pair(tmp_path):
    """Create sample video and overlay files for testing."""
    base_file = tmp_path / "2023-01-15_143000_Video_xyz98765.mp4"
    overlay_file = tmp_path / "2023-01-15_143000_Video_xyz98765_overlay.png"

    # Create minimal files with MP4 and PNG magic bytes
    base_file.write_bytes(b'\x00\x00\x00\x20ftyp' + b'\x00' * 100)  # MP4 magic bytes
    overlay_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # PNG magic bytes

    return {'base': base_file, 'overlay': overlay_file, 'sid': 'xyz98765'}


# ===== Mock Data Fixtures =====

@pytest.fixture
def mock_memory_with_location():
    """Provide a memory dict with GPS location."""
    return {
        'date': '2023-01-15 14:30:00 UTC',
        'media_type': 'Image',
        'location': 'Latitude, Longitude: 42.438072, -82.91975',
        'download_url': 'https://example.com/download?sid=abc12345',
        'sid': 'abc12345'
    }


@pytest.fixture
def mock_memory_without_location():
    """Provide a memory dict without GPS location."""
    return {
        'date': '2023-01-16 10:20:00 UTC',
        'media_type': 'Video',
        'location': '',
        'download_url': 'https://example.com/download?sid=xyz98765',
        'sid': 'xyz98765'
    }


# ===== Utility Fixtures =====

@pytest.fixture
def temp_working_dir(tmp_path, monkeypatch):
    """Change working directory to a temporary directory for the test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ===== Pytest Configuration Hooks =====

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers."""
    for item in items:
        # Add 'unit' marker to all tests by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
