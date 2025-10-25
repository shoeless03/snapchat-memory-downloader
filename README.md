
I am not a bot but the rest of this is. Created with that claude fucker.
This assumes you've exported your data and they sent you something like my_data_blah blah folder (after extracting zip) with html in it.

Recommended you create a new folder and place this whole repo inside. 
move the folder from snapchat (after extracting zip) into same folder.
change that folder name to "data from snapchat".

download_snapchat_memories.py (or snapchat-memories-downloader.exe from releases) should be at the same level as the folder you downloaded and renamed.

see below for futher usage.

End human.

claude wants coffee tho: [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X21N8LO2)

## Download

**Pre-built executables available** - No Python installation required!

Download the latest release for your platform:
- [**Windows**](../../releases/latest) - `snapchat-memories-downloader.exe` (~20MB)
- [**macOS**](../../releases/latest) - Coming soon
- [**Linux**](../../releases/latest) - Coming soon

**What's bundled:** Python + core libraries (requests, Pillow, pywin32)
**Optional downloads:** FFmpeg (video overlays) and ExifTool (GPS metadata) - see below

**Or install from source** (requires Python 3.11+):
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

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/shoeless03/snapchat-memory-downloader.git
   cd snapchat-memory-downloader
   ```

2. **Install Python dependencies:**
   ```bash
   pip install requests

   # Optional: For Windows users who want creation timestamps
   pip install pywin32
   ```

3. **Get your Snapchat data:**

** human here - claude made this shit up. idk how true it is. end human **

   - Go to [Snapchat Account Settings](https://accounts.snapchat.com/)
   - Navigate to "My Data" → "Submit Request"
   - Select "Memories" and download your data
   - Extract the ZIP file you receive from Snapchat

## Usage

### First Run

Place the Snapchat HTML file at `data from snapchat/html/memories_history.html`, then run:

```bash
python download_snapchat_memories.py
```

**What happens on first run:**
1. The script checks for optional dependencies (ExifTool, pywin32)
2. If any are missing, you'll see a prompt:
   ```
   ======================================================================
   OPTIONAL DEPENDENCIES
   ======================================================================

   The following optional features are not available:

     • ExifTool: Required for GPS metadata embedding

   What would you like to do?
     1. Continue without these features
     2. Quit to install dependencies (recommended)
   ======================================================================
   ```
3. Choose option 1 to proceed or option 2 to install dependencies first
4. The script downloads all memories with progress tracking

**The script automatically:**
- Parses the HTML to find all memories
- Downloads each memory with a 2-second delay between requests
- Embeds GPS coordinates (if ExifTool is available)
- Sets file creation timestamps (if pywin32 is available on Windows)
- Saves files to the `memories/` folder with organized subfolders
- Tracks progress in `download_progress.json`

### Re-running After Installing Dependencies

If you initially ran without ExifTool or pywin32, you can install them later:

```bash
# Install ExifTool (see Prerequisites section for platform-specific instructions)
# Then re-run the script:
python download_snapchat_memories.py
```

The script will automatically update your existing files with GPS metadata and proper timestamps!

### Command-Line Options

#### Download Options
```bash
# Basic download
python download_snapchat_memories.py

# Download with custom settings
python download_snapchat_memories.py --html "path/to/memories_history.html" --output "my_memories" --delay 3.0

# Verify what's been downloaded
python download_snapchat_memories.py --verify
```

#### Overlay Compositing Options
```bash
# Composite all overlays onto images and videos
python download_snapchat_memories.py --apply-overlays

# Composite only images (faster, skips videos)
python download_snapchat_memories.py --apply-overlays --images-only

# Composite only videos (skips images)
python download_snapchat_memories.py --apply-overlays --videos-only

# Force rebuild of overlay pairs cache
python download_snapchat_memories.py --apply-overlays --rebuild-cache

# Verify which files have been composited
python download_snapchat_memories.py --verify-composites
```

#### Timezone Conversion
human here: 
still experimental. currently just converts everything in to your current timezone (where you are running the script)
end human
```bash
# Convert all file timestamps and filenames from UTC to local timezone
python download_snapchat_memories.py --convert-timezone

# Safe to run multiple times - automatically skips already converted files
```

#### All Available Options

**Download Options:**
- `--html PATH` - Path to memories HTML file (default: `data from snapchat/html/memories_history.html`)
- `--output PATH` - Output directory (default: `memories`)
- `--delay SECONDS` - Seconds between downloads (default: 2.0, increase if rate limited)
- `--verify` - Check download status without downloading

**Overlay Compositing Options:**
- `--apply-overlays` - Composite overlay PNGs onto base images and videos (automatically copies GPS/EXIF metadata if ExifTool is available)
- `--images-only` - Only composite overlays onto images (skip videos)
- `--videos-only` - Only composite overlays onto videos (skip images)
- `--verify-composites` - Verify which files have been composited
- `--rebuild-cache` - Force rebuild of overlay pairs cache

**Timezone Conversion Options:**
- `--convert-timezone` - Convert all file timestamps and filenames from UTC to local timezone

### Handling Rate Limits

If you encounter "File is not a zip file" errors or HTTP 429 responses, Snapchat is rate-limiting you. Increase the delay:

```bash
python download_snapchat_memories.py --delay 5.0
```

The script automatically retries rate-limited downloads with exponential backoff.

## Output Structure

```
memories/
├── images/                          # Downloaded base images
│   └── 2025-10-16_194703_Image_9ce001ca.jpg
├── videos/                          # Downloaded base videos
│   └── 2025-10-15_223151_Video_9f9eb970.mp4
├── overlays/                        # Snapchat overlays (stickers, text, filters)
│   └── 2025-10-16_194703_Image_9ce001ca_overlay.png
└── composited/                      # Images/videos with overlays applied
    ├── images/
    │   └── 2025-10-16_194703_Image_9ce001ca_composited.jpg
    └── videos/
        └── 2025-10-15_223151_Video_9f9eb970_composited.mp4
```

**Filename format:** `YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext`
- Date with dashes for readability
- Time in 24-hour format
- Media type (Image/Video)
- First 8 characters of Snapchat session ID (unique identifier)
- Composited files add `_composited` suffix

## Overlay Compositing

After downloading your memories, you can composite the Snapchat overlays (stickers, text, filters, timestamps) back onto your images and videos to recreate the original look.

### How It Works

1. **Snapchat provides overlays separately**: When you download memories, overlays come as transparent PNG files
2. **The script matches overlays to media**: Using filename patterns to pair each overlay with its base file
3. **Compositing creates new files**: Original files remain untouched, composited versions saved to `memories/composited/`
4. **Fast processing**: ~10 images/second (or ~0.6 images/second with ExifTool for automatic metadata copying), uses caching for instant restarts

### Quick Start

```bash
# Composite all overlays (images and videos)
python download_snapchat_memories.py --apply-overlays

# Only composite images (much faster)
python download_snapchat_memories.py --apply-overlays --images-only
```

### Performance Options

**Without ExifTool:**
- ~10 images/second
- File timestamps preserved
- No GPS/EXIF metadata copying
```bash
python download_snapchat_memories.py --apply-overlays --images-only
```

**With ExifTool installed:**
- ~0.6 images/second (slower due to automatic EXIF copying)
- Automatically preserves all GPS and EXIF metadata
- ExifTool is automatically detected and used
```bash
# ExifTool will be detected and used automatically
python download_snapchat_memories.py --apply-overlays
```

### Verification and Resuming

```bash
# Check what's been composited
python download_snapchat_memories.py --verify-composites

# Shows:
# - Total overlay pairs found
# - Successfully composited images/videos
# - Failed composites (with error details)
# - Missing composites (not yet attempted)
```

The script tracks compositing progress, so you can:
- Interrupt and resume at any time
- Automatically skip already-composited files
- Retry failed composites

### Troubleshooting Composites

**Failed composites are tracked** in `download_progress.json` under `failed_composites`. Common issues:
- **0-byte overlay files**: Empty overlays from Snapchat (corrupt downloads)
- **Missing dependencies**: Pillow for images, FFmpeg for videos
- **Corrupt overlay images**: Run `--verify-composites` to identify

## Resume & Progress Tracking

The script tracks progress in `download_progress.json`. If interrupted:
- Re-run the script - it will skip already-downloaded files
- Already-downloaded files will have their metadata updated if new dependencies are installed
- Failed downloads are tracked and automatically retried (up to 5 attempts)
- Failed composites are tracked separately with error messages
- Use `--verify` to check download status
- Use `--verify-composites` to check compositing status

## Platform Support

| Feature | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Modification Time | ✅ Always | ✅ Always | ✅ Always |
| Creation Time | ✅ Built-in | ✅ Built-in | ⚠️ Requires pywin32 |
| GPS Metadata | ✅ With ExifTool | ✅ With ExifTool | ✅ With ExifTool |

Files are sorted chronologically by Snapchat creation date, not download date.

**Dependency Detection:** The script automatically checks for ExifTool and pywin32 at startup and will prompt you if they're missing.

## Troubleshooting

### Rate Limiting
**Error:** `File is not a zip file` or `HTTP 429`

**Solution:** Increase delay between downloads:
```bash
python download_snapchat_memories.py --delay 5.0
```

### Missing Dependencies
**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:** Install requests:
```bash
pip install requests
```

### Optional Dependencies
If you skipped installing ExifTool or pywin32 initially:
1. Install the missing dependency (see Prerequisites section)
2. Re-run the script - it will automatically update your existing files!

### Download Failures
Check `download_progress.json` for error details. Re-run the script to retry failed downloads.

## Documentation

For detailed information, see [CLAUDE.md](CLAUDE.md) which includes:
- Complete feature documentation
- File structure analysis
- Implementation details
- Snapchat export format explanation
- Advanced troubleshooting

## Requirements

- Python 3.7 or higher ([python.org](https://www.python.org/))
- requests library ([PyPI - requests](https://pypi.org/project/requests/))
- pywin32 library (Windows only, optional) ([PyPI - pywin32](https://pypi.org/project/pywin32/))

## License

MIT License - see [LICENSE](LICENSE) file for details.

This project is provided as-is for personal use to download your own Snapchat memories.

## Pre-built Executables

Pre-built executables are available for download in [Releases](../../releases/latest).

**Benefits:**
- No Python installation required
- No dependency management
- All libraries bundled
- Just download and run

**What's included:**
- The complete application
- All required Python libraries (requests, Pillow, pywin32)
- Third-party licenses and attribution

**What's NOT included (optional):**
- FFmpeg (for video overlay compositing) - [Download separately](https://ffmpeg.org)
- ExifTool (for GPS metadata) - [Download separately](https://exiftool.org)

See [BUILD-INSTRUCTIONS.md](BUILD-INSTRUCTIONS.md) for building from source.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created with [Claude Code](https://claude.com/claude-code) for organizing Snapchat memories exports.

---

**Note:** This tool is for downloading your own personal Snapchat data. Respect Snapchat's rate limits and terms of service.
