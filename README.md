
I am not a bot but the rest of this is. Created with Claude Code - use at your own risk.

This assumes you've exported your data and they sent you something like my_data_blah blah folder with html in it.

change that folder name to "data from snapchat" and this script should be at the same level as the folder you downloaded and renamed.

You can figure it out from there right? 

;] 

see below ai slop for futher usage.

works on my machine.
 
end human.

## Overview

This tool automatically downloads all your Snapchat memories (photos and videos) from the HTML export file, organizing them with human-readable filenames and preserving the original creation timestamps.

**Key Features:**
- 📁 Organizes files into `images/`, `videos/`, and `overlays/` folders
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
- **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
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

```bash
# Download with custom settings
python download_snapchat_memories.py --html "path/to/memories_history.html" --output "my_memories" --delay 3.0

# Verify what's been downloaded
python download_snapchat_memories.py --verify
```

**Available options:**
- `--html` - Path to memories HTML file (default: `data from snapchat/html/memories_history.html`)
- `--output` - Output directory (default: `memories`)
- `--delay` - Seconds between downloads (default: 2.0, increase if rate limited)
- `--verify` - Check download status without downloading

### Handling Rate Limits

If you encounter "File is not a zip file" errors or HTTP 429 responses, Snapchat is rate-limiting you. Increase the delay:

```bash
python download_snapchat_memories.py --delay 5.0
```

The script automatically retries rate-limited downloads with exponential backoff.

## Output Structure

```
memories/
├── images/
│   └── 2025-10-16_194703_Image_9ce001ca.jpg
├── videos/
│   └── 2025-10-15_223151_Video_9f9eb970.mp4
└── overlays/
    └── 2025-10-16_194703_Image_9ce001ca_overlay.png
```

**Filename format:** `YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext`
- Date with dashes for readability
- Time in 24-hour format
- Media type (Image/Video)
- First 8 characters of Snapchat session ID (unique identifier)

## Resume & Progress Tracking

The script tracks progress in `download_progress.json`. If interrupted:
- Re-run the script - it will skip already-downloaded files
- Already-downloaded files will have their metadata updated if new dependencies are installed
- Failed downloads are tracked and automatically retried (up to 5 attempts)
- Use `--verify` to check what's missing

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

This project is provided as-is for personal use to download your own Snapchat memories.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created with [Claude Code](https://claude.com/claude-code) for organizing Snapchat memories exports.

---

**Note:** This tool is for downloading your own personal Snapchat data. Respect Snapchat's rate limits and terms of service.
