
I am not a bot but the rest of this is. Created with that claude fucker.
This assumes you've exported your data and they sent you something like my_data_blah blah folder (after extracting zip) with html in it.

Recommended you 
- create a new folder and place this whole repo inside
  - (FOR EACH EXPORT!!! IDK what will happen if you replace the html with a newly exported html! it should never delete files but i don't recommend this!)
- move the folder from snapchat (after extracting zip) into same folder.
- change that folder (my_data_blah blah folder) name to "data from snapchat".



download_snapchat_memories.py (or snapchat-memories-downloader.exe from releases) should be at the same level as the folder you downloaded and renamed.

see below for futher usage.

End human.

claude wants coffee tho: [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X21N8LO2)

## Download

### Less tech experience
Will be not as up to date. See your downloaded release post for more info.

**Pre-built executables available** - No Python installation required!

Download the latest release for your platform:
- [**Windows**](../../releases/latest) - `snapchat-memories-downloader.exe` (~20MB)
- [**macOS**](../../releases/latest) - Coming soon
- [**Linux**](../../releases/latest) - Coming soon

**What's bundled:** Python + core libraries (requests, Pillow, pywin32)
**Optional downloads:** FFmpeg (video overlays) and ExifTool (GPS metadata) - see below

### 🐱RECOMMENDED🙀:
**install from source** (requires Python 3.11+):
```bash
git clone https://github.com/shoeless03/snapchat-memory-downloader.git
cd snapchat-memory-downloader
pip install requests
python download_snapchat_memories.py
```

## Overview

This tool automatically downloads all your Snapchat memories (photos and videos) from the HTML export file, organizing them with human-readable filenames and preserving the original creation timestamps.

**Key Features:**
- 📁 Organizes files into `images/`, `videos/`, and `overlays/` folders
- 🎨 **Overlay compositing** - Combine Snapchat overlays (stickers, text, filters) back onto your photos and videos
- 📅 Human-readable filenames with timestamps (e.g., `2025-10-16_194703_Image_9ce001ca.jpg`)
- ⏰ Preserves Snapchat creation dates in file metadata
- 📍 Automatic GPS coordinate embedding when ExifTool is installed
- 🔄 Resume capability - tracks progress and skips already-downloaded files
- 🛡️ Rate limit handling with automatic retry and exponential backoff
- ✅ Verification mode to check download completeness
- 🔍 Smart dependency detection with user prompts
- 🖥️ Cross-platform support (Linux, macOS, Windows)

## Prerequisites

### Required
- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **requests library** - Install with: `pip install requests`

### Optional Dependencies

The script will automatically detect these at startup and prompt you if they're missing:

**For embedding GPS coordinates in files:**
- **ExifTool** - [Download ExifTool](https://exiftool.org/)
  - **Windows**: Download from https://exiftool.org/ and extract to the script folder as `exiftool-13.39_64/`
  - **Linux**: `sudo apt install libimage-exiftool-perl` or `sudo dnf install perl-Image-ExifTool`
  - **macOS**: `brew install exiftool`
  - If detected, GPS coordinates will be automatically embedded in your photos and videos

**For setting file creation timestamps (Windows only):**
- **pywin32** - Install with: `pip install pywin32`
  - Not needed on Linux or macOS (built-in support)
  - Without it, modification times will still be set correctly on Windows

**For compositing overlays onto images:**
- **Pillow** - Install with: `pip install pillow` or `pip install pillow-simd` (5x faster)
  - Required to composite Snapchat overlays (stickers, text, filters) onto your images
  - Creates new files in `memories/composited/images/` folder

**For compositing overlays onto videos:**
- **FFmpeg** - [Download FFmpeg](https://ffmpeg.org/download.html)
  - **Windows**: Download from https://ffmpeg.org/download.html and add to PATH
  - **Linux**: `sudo apt install ffmpeg` or `sudo dnf install ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - Required to composite Snapchat overlays onto your videos
  - Creates new files in `memories/composited/videos/` folder

> **Note:** You can run the script without these dependencies! If missing, you'll be prompted with:
> - Option to continue without the optional features
> - Option to quit and install them first
>
> You can also install them later and re-run the script to automatically update your existing files.

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
- **[Testing Guide](tests/TESTING.md)** - Unit tests and testing documentation

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
pip install -r tests/requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=scripts --cov-report=html
```

**Test Suite:** 138+ passing tests covering all functionality. See [TESTING.md](tests/TESTING.md) for details.

### Contributing

This project is organized for clarity:
- Source code in `scripts/`
- Documentation in `docs/`
- Build tools in `tools/build/`
- Tests in `tests/`

See [docs/CLAUDE.md](docs/CLAUDE.md) for implementation details.
