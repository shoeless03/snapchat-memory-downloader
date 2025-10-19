
I am not a bot but the rest of this is. Created with claude code use at your own risk.

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
- 🔄 Resume capability - tracks progress and skips already-downloaded files
- 🛡️ Rate limit handling with automatic retry and exponential backoff
- ✅ Verification mode to check download completeness
- 🖥️ Cross-platform support (Linux, macOS, Windows)

## Prerequisites

### Required
- **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
- **requests library** - Install with: `pip install requests`

### Optional (for setting file creation timestamps)
- **pywin32** (Windows only) - Install with: `pip install pywin32`
  - Not needed on Linux or macOS (built-in support)

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

### Basic Download

Place the Snapchat HTML file at `data from snapchat/html/memories_history.html`, then run:

```bash
python download_snapchat_memories.py
```

The script will:
- Parse the HTML to find all memories
- Download each memory with a 2-second delay between requests
- Save files to the `memories/` folder with organized subfolders
- Track progress in `download_progress.json`

### Command-Line Options

```bash
# Download with custom settings
python download_snapchat_memories.py --html "path/to/memories_history.html" --output "my_memories" --delay 3.0

# Verify what's been downloaded
python download_snapchat_memories.py --verify

# Update existing files to new naming format and timestamps
python download_snapchat_memories.py --update-filenames
```

**Available options:**
- `--html` - Path to memories HTML file (default: `data from snapchat/html/memories_history.html`)
- `--output` - Output directory (default: `memories`)
- `--delay` - Seconds between downloads (default: 2.0, increase if rate limited)
- `--verify` - Check download status without downloading
- `--update-filenames` - Rename existing files and update timestamps

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
- Failed downloads are tracked and automatically retried (up to 5 attempts)
- Use `--verify` to check what's missing

## Platform Support

| Platform | Modification Time | Creation Time |
|----------|------------------|---------------|
| Linux    | ✅ Always set     | ✅ Built-in   |
| macOS    | ✅ Always set     | ✅ Built-in   |
| Windows  | ✅ Always set     | ⚠️ Requires pywin32 |

Files are sorted chronologically by Snapchat creation date, not download date.

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
