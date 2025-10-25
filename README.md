# Snapchat Memories Downloader

Download and organize your Snapchat memories from the "Download My Data" export with proper timestamps, overlay compositing, and GPS metadata.

## Quick Start

```bash
# Install dependencies
pip install requests Pillow

# Download all memories
python download_snapchat_memories.py

# Apply overlays to recreate original Snapchat look
python download_snapchat_memories.py --apply-overlays
```

## Documentation

- **[User Guide](docs/README.md)** - Complete usage instructions and features
- **[Developer Guide](docs/CLAUDE.md)** - Project architecture and implementation details
- **[Build Instructions](docs/BUILD-INSTRUCTIONS.md)** - How to create executables for distribution
- **[Testing Guide](TESTING.md)** - Unit tests and testing documentation

## Project Structure

```
snap2/
├── download_snapchat_memories.py    # Main entry point
├── scripts/                          # Python source modules
│   ├── cli.py                       # Command-line interface
│   ├── downloader.py                # Download orchestration
│   ├── compositor.py                # Overlay compositing
│   ├── metadata.py                  # GPS/EXIF metadata
│   ├── progress.py                  # Progress tracking
│   ├── snap_config.py               # Configuration
│   └── snap_parser.py               # HTML parsing
├── docs/                            # Documentation
│   ├── README.md                    # User guide
│   ├── CLAUDE.md                    # Developer guide
│   ├── BUILD-INSTRUCTIONS.md        # Build guide
│   └── LICENSE                      # MIT License
├── tools/                           # Build and development tools
│   ├── build/                       # Build scripts and spec files
│   └── exiftool/                    # ExifTool binary (optional)
├── tests/                           # Test files
├── data from snapchat/              # Your Snapchat export (you provide this)
│   └── html/
│       └── memories_history.html
└── memories/                        # Downloaded memories (created by script)
    ├── images/
    ├── videos/
    ├── overlays/
    └── composited/
```

## Features

✅ **Smart Downloads**
- Resume interrupted downloads
- Automatic retry with rate limit handling
- Progress tracking in `download_progress.json`

✅ **Overlay Compositing**
- Recreate original Snapchat look with stickers, text, and filters
- Fast processing: ~10 images/second
- Automatic GPS/EXIF metadata copying (if ExifTool available)

✅ **Timezone Support**
- Files downloaded in UTC by default
- Convert to local timezone with `--convert-timezone`

✅ **Proper File Naming**
- Format: `YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext`
- Example: `2025-10-16_194703_Image_9ce001ca.jpg`

✅ **File Timestamps**
- Modification time set to Snapchat creation date
- Creation/birth time preserved on Linux/macOS/Windows

## Requirements

- Python 3.11+
- `requests` package (required)
- `Pillow` package (optional, for image overlay compositing)
- FFmpeg (optional, for video overlay compositing)
- ExifTool (optional, for GPS/EXIF metadata preservation)

## Common Commands

```bash
# Verify downloads
python download_snapchat_memories.py --verify

# Apply overlays only to images (faster)
python download_snapchat_memories.py --apply-overlays --images-only

# Convert timestamps to local timezone
python download_snapchat_memories.py --convert-timezone

# Custom HTML path and output directory
python download_snapchat_memories.py --html "path/to/memories_history.html" --output "my_memories"
```

## License

MIT License - see [docs/LICENSE](docs/LICENSE)

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=scripts --cov-report=html
```

**Test Suite:** 138+ passing tests covering all functionality. See [TESTING.md](TESTING.md) for details.

### Contributing

This project is organized for clarity:
- Source code in `scripts/`
- Documentation in `docs/`
- Build tools in `tools/build/`
- Tests in `tests/`

See [docs/CLAUDE.md](docs/CLAUDE.md) for implementation details.
