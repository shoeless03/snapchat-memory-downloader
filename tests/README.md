# Snapchat Memories Downloader - Test Suite

This directory contains comprehensive unit and integration tests for the Snapchat Memories Downloader project.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and pytest configuration
├── test_snap_parser.py            # Tests for HTML parsing
├── test_metadata.py               # Tests for file metadata operations
├── test_compositor.py             # Tests for overlay compositing
├── test_progress.py               # Tests for progress tracking
├── test_timezone_converter.py     # Tests for timezone conversion
├── test_snap_config.py            # Tests for configuration and dependency checking
├── test_gps.py                    # GPS metadata testing (existing)
└── README.md                      # This file
```

## Running Tests

### Prerequisites

Install pytest and optional testing dependencies:

```bash
pip install pytest pytest-cov pytest-mock
```

### Run All Tests

```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=scripts --cov-report=html
```

### Run Specific Test Files

```bash
# Test a specific module
pytest tests/test_snap_parser.py

# Test a specific class
pytest tests/test_metadata.py::TestParseLocation

# Test a specific function
pytest tests/test_metadata.py::TestParseLocation::test_parse_location_valid
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## Test Categories

### Unit Tests

- **test_snap_parser.py**: Tests HTML parsing logic, table row extraction, SID parsing
- **test_metadata.py**: Tests timestamp setting, GPS coordinate parsing, metadata operations
- **test_compositor.py**: Tests overlay pair finding, image/video compositing
- **test_progress.py**: Tests download tracking, failure recording, verification
- **test_timezone_converter.py**: Tests UTC to local conversion, filename generation
- **test_snap_config.py**: Tests dependency detection and user prompts

### Integration Tests

(To be added as needed)

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_html_file`: Creates a test HTML file with sample memories
- `sample_memories`: Provides sample memory dictionaries
- `output_directory_structure`: Creates standard output directory structure
- `progress_file`: Creates a temporary progress JSON file
- `sample_image_pair`: Creates test image and overlay files
- `sample_video_pair`: Creates test video and overlay files
- `mock_memory_with_location`: Memory with GPS coordinates
- `mock_memory_without_location`: Memory without GPS coordinates

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<Feature>`
- Test functions: `test_<what_is_being_tested>`

### Example Test

```python
def test_parse_location_valid():
    """Test parsing valid GPS coordinates."""
    memory = {'location': 'Latitude, Longitude: 42.438072, -82.91975'}
    coords = parse_location(memory)

    assert coords is not None
    assert coords[0] == 42.438072
    assert coords[1] == -82.91975
```

### Using Fixtures

```python
def test_with_fixture(sample_memories):
    """Test using a fixture."""
    assert len(sample_memories) == 3
    assert sample_memories[0]['media_type'] == 'Image'
```

### Mocking External Dependencies

```python
from unittest.mock import patch, Mock

@patch('subprocess.run')
def test_with_mock(mock_run):
    """Test with mocked subprocess."""
    mock_run.return_value = Mock(returncode=0)
    # Your test code here
```

## Test Coverage

To generate a coverage report:

```bash
pytest --cov=scripts --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view the detailed coverage report.

## Continuous Integration

These tests are designed to run in CI/CD environments. They:

- Don't require actual Snapchat data
- Use temporary directories for file operations
- Mock external dependencies (exiftool, ffmpeg, network requests)
- Are platform-aware (skip platform-specific tests as appropriate)

## Platform-Specific Tests

Some tests are platform-specific:

- Windows-only tests check for `pywin32` functionality
- Unix-specific tests may check different timestamp behaviors

Use pytest's skip markers:

```python
@pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
def test_windows_feature():
    # Windows-only test
```

## Troubleshooting

### Import Errors

If you see import errors, ensure:
1. You're running tests from the project root
2. The `scripts/` directory is in the Python path (conftest.py handles this)

### Missing Dependencies

Some tests require optional dependencies:
- Pillow/PIL (for image tests)
- FFmpeg (mocked in tests, but some integration tests may need it)
- pywin32 (Windows only)

These dependencies are mocked in unit tests, so they're not required to run the test suite.

## Contributing

When adding new functionality:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Aim for >80% code coverage
4. Include both positive and negative test cases
5. Test edge cases and error handling

## License

Same as main project.
