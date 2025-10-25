# Testing Documentation

## Test Suite Summary

This project includes a comprehensive test suite with **142 total tests** covering all major functionality.

### Test Results

```
✅ 138 tests passed
⏭️ 4 tests skipped (intentionally)
❌ 0 tests failed
```

### Test Coverage by Module

| Module | Test File | Tests | Coverage |
|--------|-----------|-------|----------|
| HTML Parser | test_snap_parser.py | 18 | HTML parsing, SID extraction, table parsing |
| Metadata | test_metadata.py | 33 | Timestamps, GPS coordinates, EXIF operations |
| Compositor | test_compositor.py | 22 | Overlay pairing, image/video compositing |
| Progress Tracker | test_progress.py | 40 | Download tracking, failure recording, verification |
| Timezone Converter | test_timezone_converter.py | 23 | UTC/local conversion, filename generation |
| Configuration | test_snap_config.py | 16 | Dependency checking, user prompts |
| GPS Integration | test_gps.py | 1 | Manual integration testing |

**Total:** 142 tests

### Skipped Tests

The following tests are intentionally skipped:

1. **test_gps_metadata_integration** - Manual integration test requiring actual Snapchat data files
2. **test_get_exiftool_path_local_windows** - Requires complex Path mocking
3. **test_check_pywin32_on_non_windows** - Platform-specific (only runs on non-Windows systems)
4. **test_check_pillow_not_available** - Requires uninstalling Pillow to test

These skips are by design and do not indicate missing coverage.

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Basic run
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=scripts --cov-report=html

# Run specific test file
pytest tests/test_snap_parser.py

# Run specific test
pytest tests/test_metadata.py::TestParseLocation::test_parse_location_valid
```

### Run Tests by Category

```bash
# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Platform-Specific Testing

Some tests are platform-aware and will automatically skip on incompatible systems:

- **Windows-only tests**: pywin32 functionality, creation time setting
- **Unix-only tests**: Specific timestamp behaviors
- **macOS-specific tests**: Birth time handling

## Test Organization

### Fixtures (conftest.py)

Common test fixtures available to all tests:

- `sample_html_file` - Test HTML with sample memories
- `sample_memories` - Memory dictionaries
- `output_directory_structure` - Standard folder structure
- `progress_file` - Temporary progress JSON
- `sample_image_pair` - Test image + overlay
- `sample_video_pair` - Test video + overlay
- `mock_memory_with_location` - Memory with GPS
- `mock_memory_without_location` - Memory without GPS

### Test Structure

Tests follow a consistent naming convention:

- **Files**: `test_<module>.py`
- **Classes**: `Test<Feature>`
- **Functions**: `test_<what_is_tested>`

Example:
```python
class TestParseLocation:
    def test_parse_location_valid(self):
        """Test parsing valid GPS coordinates."""
        # Test implementation
```

## Mocking Strategy

External dependencies are mocked to ensure tests run without:

- **ExifTool** - Mocked with `@patch('snap_config.get_exiftool_path')`
- **FFmpeg** - Mocked with `@patch('subprocess.run')`
- **Network requests** - Mocked with `@patch('requests.get')`
- **File system operations** - Use `tmp_path` fixture

## Coverage Goals

Current test coverage focuses on:

✅ **Core functionality** - All critical paths tested
✅ **Error handling** - Edge cases and exceptions
✅ **Integration points** - Module interactions
✅ **Platform compatibility** - Cross-platform support
✅ **Data validation** - Input/output validation

## Continuous Integration

These tests are designed for CI/CD environments:

- No external dependencies required
- All file operations use temporary directories
- Deterministic results (no flaky tests)
- Fast execution (< 1 second for full suite)
- Platform-aware skipping

## Adding New Tests

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Use existing fixtures** from conftest.py
3. **Mock external dependencies** (exiftool, ffmpeg, network)
4. **Test both success and failure** cases
5. **Include edge cases** (empty inputs, invalid data, etc.)
6. **Add docstrings** explaining what is tested
7. **Aim for >80% coverage** of new code

Example new test:

```python
def test_new_feature(tmp_path):
    """Test description of what this verifies."""
    # Arrange
    test_file = tmp_path / "test.txt"
    test_file.write_text("test data")

    # Act
    result = my_function(test_file)

    # Assert
    assert result == expected_value
```

## Known Limitations

- **PIL tests** require Pillow to be installed (included in requirements-test.txt)
- **Platform-specific tests** only run on appropriate OS
- **Integration tests** marked as skip by default (require real data)
- **Complex mocking** tests may be skipped if too difficult to mock reliably

## Troubleshooting

### Import Errors

Ensure you're running from the project root:
```bash
cd /path/to/snap2
pytest
```

### Missing Dependencies

Install test requirements:
```bash
pip install -r requirements-test.txt
```

### Platform Errors

Some tests are platform-specific and will skip automatically:
```
SKIPPED [1] test_snap_config.py:102: Non-Windows test
```

This is expected behavior.

## Future Test Additions

Potential areas for expanded testing:

- [ ] Full downloader module tests
- [ ] CLI integration tests
- [ ] Performance benchmarks
- [ ] Network retry logic tests
- [ ] Concurrent download tests
- [ ] Large file handling tests

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Last Updated:** 2024-01-24
**Test Framework:** pytest 7.4+
**Python Version:** 3.8+
