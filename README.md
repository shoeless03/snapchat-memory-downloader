June 2026:
I'm no longer updating this atm. I think snapchat has altered how they serve they're backups at this point to make this tool out of date. But feel free to try/fork your own.





I am not a bot but the rest of this is. Created with that claude fucker.
This assumes you've exported your data and they sent you something like my_data_blah blah folder (after extracting zip) with html in it.




Added pre-built releases for all platforms -------------------------------->>>>>>>>>>>>>>>>>>>>>>>>>>
https://github.com/shoeless03/snapchat-memory-downloader/releases


I don't have a Mac so let me know if it works.



Recommended you 
- create a new folder **for each export** and place this program inside. 
- move the folder from snapchat (after extracting zip) into same folder.
- change that folder (my_data_blah blah folder) name to "data from snapchat".


download release or follow build instructions below.


snapchat gives the original video/image and the overlay as seperate files, this scipt doesn't remove them, just origanizes them.
You can re-create the effect with the menu to create new images/vidoes with the snapchat overlay embedded (leaving originals untouched) in a new folder.

see below for futher usage.

**If this tool has helped you and you feel like contributing please consider donating to Palestine Children's Relief Fund: https://www.pcrf.net/donate**

**contributing: If you submit a pr you MUST disclose if ai was used in your code generation!!!.**

End human.

## Download

**Pre-built executables available** - No Python installation required!

Download the latest release for your platform:
- [**Windows**](../../releases/latest)
- [**macOS**](../../releases/latest)
- [**Linux**](../../releases/latest)

**What's bundled:** Python + core libraries (requests, Pillow, pywin32)
**Optional downloads:** FFmpeg (video overlays) and ExifTool (GPS metadata) - see below


OR


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
- 🎯 **Interactive menu** - User-friendly interface with arrow key navigation (no command-line expertise needed!)
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

## Quick Start

**Want to get started in under 5 minutes?** Here's the fastest path:

### Step 1: Set Up the Tool

**Option A: Use Pre-Built Executable (No Python Required)**
1. Download the [latest release](../../releases/latest) for your platform
2. Extract the ZIP file
3. Place your Snapchat data folder next to the executable and rename it to `data from snapchat`

**Option B: Run from Source (Requires Python 3.11+)**
```bash
git clone https://github.com/shoeless03/snapchat-memory-downloader.git
cd snapchat-memory-downloader
pip install requests questionary
```

### Step 2: Organize Your Files

Your folder structure should look like this:
```
snapchat-memory-downloader/          # The tool
├── snapchat-memories-downloader.exe  # (or download_snapchat_memories.py)
└── data from snapchat/               # Your Snapchat export (rename to exactly this)
    └── html/
        └── memories_history.html
```

### Step 3: Run the Downloader

**Using executable:**
```bash
./snapchat-memories-downloader.exe
```

**Using Python:**
```bash
python download_snapchat_memories.py
```

The script will:
- Launch an interactive menu (use ↑/↓ arrow keys to navigate)
- Check for optional dependencies (ExifTool, FFmpeg, etc.)
- Prompt you if any are missing (you can continue without them)
- Download all your memories to a `memories/` folder
- Track progress so you can resume if interrupted

### Step 4: Optional Enhancements

Once your memories are downloaded:

**Apply overlays** (stickers, text, filters):
```bash
python download_snapchat_memories.py --apply-overlays
```

**Convert timestamps to GPS-based local timezones:**
```bash
python download_snapchat_memories.py --convert-timezone
```

**Check what's been downloaded:**
```bash
python download_snapchat_memories.py --verify
```

That's it! Your memories will be organized in the `memories/` folder with human-readable filenames and proper timestamps.

---

## Prerequisites

### Required
- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **requests library** - Install with: `pip install requests`
- **questionary** (for interactive menu) - Install with: `pip install questionary`

### Optional Dependencies

The script will automatically detect these at startup and prompt you if they're missing:

**For embedding GPS coordinates in files:**
- **ExifTool** - [Download ExifTool](https://exiftool.org/)
  - **Windows**: Download from https://exiftool.org/ and extract to `tools/exiftool/` folder
  - **Linux**: `sudo apt install libimage-exiftool-perl` or `sudo dnf install perl-Image-ExifTool`
  - **macOS**: `brew install exiftool`
  - If detected, GPS coordinates will be automatically embedded in your photos and videos

**For setting file creation timestamps (Windows only):**
- **pywin32** - Install with: `pip install pywin32`
  - Not needed on Linux or macOS (built-in support)
  - Without it, modification times will still be set correctly on Windows

**For compositing overlays onto images:**
- **Pillow** - Install with: `pip install pillow`
  - Required to composite Snapchat overlays (stickers, text, filters) onto your images
  - Creates new files in `memories/composited/images/` folder

**For compositing overlays onto videos:**
- **FFmpeg** - [Download FFmpeg](https://ffmpeg.org/download.html)
  - **Windows**: Download from https://ffmpeg.org/download.html and add to PATH
  - **Linux**: `sudo apt install ffmpeg` or `sudo dnf install ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - Required to composite Snapchat overlays onto your videos
  - Creates new files in `memories/composited/videos/` folder

**For GPS-based timezone conversion:**
- **timezonefinder** - Install with: `pip install timezonefinder`
  - Required to convert timestamps from UTC to GPS-based local timezones
  - Automatically detects timezone where each photo/video was taken using GPS coordinates
- **pytz** (Python < 3.9 only) - Install with: `pip install pytz`
  - Python 3.9+ has built-in zoneinfo support (no need to install)
  - Not needed if you're using Python 3.9 or higher

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
   pip install requests questionary

   # Optional: For Windows users who want creation timestamps
   pip install pywin32
   ```

3. **Place your Snapchat data:**
   - Extract your Snapchat data export ZIP file
   - Rename the extracted folder to `data from snapchat`
   - Place it in the same directory as the script

## Usage

### Interactive Menu (Recommended)

Simply run the script without any arguments to launch the interactive menu:

```bash
python download_snapchat_memories.py
```

The interactive menu will appear with arrow key navigation:
- Use **↑/↓** arrow keys to navigate
- Press **Enter** to select
- Choose from: Download, Apply Overlays, Verify, Convert Timezone, and more

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
python download_snapchat_memories.py --download

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

Convert all file timestamps and filenames from UTC to **GPS-based timezones** where the photo/video was actually taken!

**How it works:**
1. Reads UTC dates and GPS coordinates from `download_progress.json` for each file
2. Uses GPS coordinates to detect the timezone where the memory was taken (e.g., "America/New_York", "Europe/Paris")
3. Converts timestamps to the detected timezone (falls back to system timezone if GPS not available)
4. Renames files to use local time in filenames
5. Updates file modification/creation times to local time
6. Updates EXIF metadata with proper timezone offset (e.g., "-04:00" for EDT) if ExifTool is available
7. Tracks detailed conversion info in `timezone_conversions.json`

**Requirements:**
```bash
# Required for GPS-based timezone detection
pip install timezonefinder

# Python < 3.9 only (Python 3.9+ has built-in zoneinfo)
pip install pytz
```

**Usage:**
```bash
# Convert all file timestamps and filenames from UTC to GPS-based local timezones
python download_snapchat_memories.py --convert-timezone

# Safe to run multiple times - automatically skips already converted files
```

**Examples:**

Photo taken in New York (GPS: 40.7128° N, 74.0060° W):
- Before: `2025-10-16_194703_Image_9ce001ca.jpg` (UTC: 7:47 PM)
- After: `2025-10-16_154703_Image_9ce001ca.jpg` (EDT: 3:47 PM in America/New_York timezone)
- EXIF metadata: DateTimeOriginal = "2025:10:16 15:47:03", OffsetTimeOriginal = "-04:00"

Photo taken in Paris (GPS: 48.8566° N, 2.3522° E):
- Before: `2025-10-16_194703_Image_9ce001ca.jpg` (UTC: 7:47 PM)
- After: `2025-10-16_214703_Image_9ce001ca.jpg` (CEST: 9:47 PM in Europe/Paris timezone)
- EXIF metadata: DateTimeOriginal = "2025:10:16 21:47:03", OffsetTimeOriginal = "+02:00"

**Statistics:**
After conversion, the script shows:
- Number of GPS-based conversions vs system timezone fallbacks
- List of all timezones detected with file counts
- Example: "America/New_York: 150 files, Europe/London: 25 files"

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
- `--convert-timezone` - Convert all file timestamps and filenames from UTC to GPS-based local timezones (falls back to system timezone if GPS not available)

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

For detailed information, see [docs/CLAUDE.md](docs/CLAUDE.md) which includes:
- Complete feature documentation
- File structure analysis
- Implementation details
- Snapchat export format explanation
- Advanced troubleshooting

## Requirements

- Python 3.7 or higher ([python.org](https://www.python.org/))
- requests library ([PyPI - requests](https://pypi.org/project/requests/))
- questionary library ([PyPI - questionary](https://pypi.org/project/questionary/))

**Optional:**
- pywin32 library (Windows only) ([PyPI - pywin32](https://pypi.org/project/pywin32/))
- timezonefinder library (for GPS-based timezone conversion) ([PyPI - timezonefinder](https://pypi.org/project/timezonefinder/))
- pytz library (Python < 3.9 only, for timezone conversion) ([PyPI - pytz](https://pypi.org/project/pytz/))

## License

MIT License - see [docs/LICENSE](docs/LICENSE) file for details.

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
- All required Python libraries (requests, Pillow, pywin32, questionary)
- Third-party licenses and attribution

**What's NOT included (optional):**
- FFmpeg (for video overlay compositing) - [Download separately](https://ffmpeg.org)
- ExifTool (for GPS metadata) - [Download separately](https://exiftool.org)

See [docs/BUILD-INSTRUCTIONS.md](docs/BUILD-INSTRUCTIONS.md) for building from source.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created with [Claude Code](https://claude.com/claude-code) for organizing Snapchat memories exports.

---

**Note:** This tool is for downloading your own personal Snapchat data. Respect Snapchat's rate limits and terms of service.
