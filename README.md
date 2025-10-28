
I am not a bot but the rest of this is. Created with that claude fucker.
This assumes you've exported your data and they sent you something like my_data_blah blah folder (after extracting zip) with html in it.




Added pre-built releases for all platforms -------------------------------->>>>>>>>>>>>>>>>>>>>>>>>>>
I don't have a Mac so let me know if it works.



Recommended you 
- create a new folder and place this whole repo inside
  - FOR EACH snapchat EXPORT!!!
      - IDK what will happen if you replace the html with a newly exported html! it should never delete files but i don't recommend this! until further testing done.)
- move the folder from snapchat (after extracting zip) into same folder.
- change that folder (my_data_blah blah folder) name to "data from snapchat".


download_snapchat_memories.py (or snapchat-memories-downloader.exe from releases) should be at the same level as the folder you downloaded and renamed.


snapchat gives the original video/image and the overlay, this scipt doesn't remove them, just origanizes them.
You can re-create the effect with the --apply-overlays flag (see below) to create new images/vidoes with the snapchat overlay embedded (leaving original untouched) in a new folder.


see below for futher usage.

End human.

claude wants coffee tho: [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X21N8LO2)

## Download

**Pre-built executables available** - No Python installation required! **[New user? Start here!](docs/GETTING-STARTED.md)**

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

### Interactive Menu (Recommended)

Simply run the script without any arguments to launch the interactive menu:

```bash
# Install dependencies
pip install requests Pillow questionary

# Launch interactive menu
python download_snapchat_memories.py
```

The interactive menu will appear with arrow key navigation:
- Use **↑/↓** arrow keys to navigate
- Press **Enter** to select
- Choose from: Download, Apply Overlays, Verify, Convert Timezone, and more

### Command-Line Usage

You can also use command-line arguments directly:

```bash
# Download all memories
python download_snapchat_memories.py --download

# Apply overlays to recreate original Snapchat look
python download_snapchat_memories.py --apply-overlays

# Verify what's been downloaded
python download_snapchat_memories.py --verify
```

## License

MIT License - see [docs/LICENSE](docs/LICENSE)
