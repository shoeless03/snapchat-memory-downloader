# Snapchat Memories Downloader

## Project Overview

This project downloads and organizes Snapchat memories from the HTML export files provided by Snapchat's "Download My Data" feature.

## Problem Statement

When you request your data from Snapchat, they provide:
- An HTML file (`memories_history.html`) with download links for each memory
- Each link downloads a file with a GUID name that changes on every download
- The original creation timestamps are only in the HTML, not preserved in downloaded files
- Need to download all files reliably without duplicates
- Need proper file naming that includes timestamps
- Need ability to resume interrupted downloads

## Solution

A Python script (`download_snapchat_memories.py`) that:

1. **Parses the HTML** to extract:
   - Download URLs
   - Timestamps (when the memory was created in Snapchat)
   - Media type (Image/Video)
   - Location data
   - Session IDs (SID) for unique identification

2. **Downloads and organizes** files:
   - Downloads each memory (ZIP file or direct media file)
   - Handles both formats:
     - **ZIP files**: Extracts main media file (JPG/MP4) and overlay (PNG)
     - **Direct media**: Detects video/image files using magic bytes and saves directly
   - Renames files with format: `YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext`
     - Example: `2025-10-16_194703_Image_9ce001ca.jpg`
     - More human-readable with dashes in date and capitalized type
   - Organizes into folders: `images/`, `videos/`, `overlays/`
   - Sets file timestamps to match Snapchat creation dates:
     - **Modification time**: Set on all platforms
     - **Creation time**: Set on Windows (requires pywin32, optional)

3. **Tracks progress** with `download_progress.json`:
   - Records successfully downloaded files (by SID)
   - Tracks failed downloads with error details
   - Allows resuming from where you left off
   - Prevents re-downloading existing files

4. **Provides verification**:
   - Check which files are downloaded vs missing
   - List failed downloads and retry counts
   - Summary statistics

## File Structure

```
snap2/
├── data from snapchat/
│   ├── index.html
│   └── html/
│       ├── memories_history.html    # Source HTML with download links
│       └── faq.html
├── memories/                         # Output directory
│   ├── images/                      # Downloaded images
│   │   └── YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.jpg
│   ├── videos/                      # Downloaded videos
│   │   └── YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.mp4
│   ├── overlays/                    # Snapchat overlays/stickers
│   │   └── YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX_overlay.png
│   └── composited/                  # Overlays applied to images/videos
│       ├── images/                  # Images with overlays
│       │   └── YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX_composited.jpg
│       └── videos/                  # Videos with overlays
│           └── YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX_composited.mp4
├── download_snapchat_memories.py    # Main download script
├── download_progress.json           # Progress tracking (auto-created)
├── overlay_pairs.json               # Cached overlay-to-media mappings
└── CLAUDE.md                        # This file
```

## Usage

### Requirements
- Python 3.11+
- Required packages: `requests` (install with `pip install requests`)

### Basic Usage

**Download all memories:**
```bash
python download_snapchat_memories.py
```

**Verify what's been downloaded:**
```bash
python download_snapchat_memories.py --verify
```

**Apply overlays to images and videos:**
```bash
# Composite all overlays onto images and videos
python download_snapchat_memories.py --apply-overlays

# Only composite images (faster)
python download_snapchat_memories.py --apply-overlays --images-only
```

**Verify composited files:**
```bash
python download_snapchat_memories.py --verify-composites
```

**Convert timestamps to local timezone:**
```bash
# Convert all file timestamps and filenames from UTC to your local timezone
python download_snapchat_memories.py --convert-timezone
```

**Custom options:**
```bash
python download_snapchat_memories.py --html "path/to/memories_history.html" \
                                     --output "my_memories" \
                                     --delay 2.0
```

### Command-line Arguments

**Download Options:**
- `--html`: Path to the memories HTML file (default: `data from snapchat/html/memories_history.html`)
- `--output`: Output directory for memories (default: `memories`)
- `--delay`: Delay between downloads in seconds (default: 2.0, increase if rate limited)
- `--verify`: Only verify downloads without downloading

**Overlay Compositing Options:**
- `--apply-overlays`: Composite overlay PNGs onto base images and videos (automatically copies GPS/EXIF metadata if ExifTool is available)
- `--images-only`: Only composite overlays onto images (skip videos)
- `--videos-only`: Only composite overlays onto videos (skip images)
- `--verify-composites`: Verify which files have been composited
- `--rebuild-cache`: Force rebuild of overlay pairs cache

**Timezone Conversion Options:**
- `--convert-timezone`: Convert all file timestamps and filenames from UTC to GPS-based timezone (safe to run multiple times, skips already converted files)

## Features

### Overlay Compositing

**NEW FEATURE:** The script can now composite Snapchat overlays (stickers, text, filters) back onto your images and videos!

**How it works:**
1. Snapchat provides overlays as separate PNG files with transparency
2. The script matches each overlay to its corresponding base image/video
3. Uses Pillow (for images) or FFmpeg (for videos) to composite them together
4. Creates new files in `memories/composited/` folder
5. Original files remain untouched

**Performance:**
- **~10 images/second** without ExifTool
- **~0.6 images/second** with ExifTool (automatically preserves GPS/EXIF data)
- Caches overlay-to-media mappings for instant startup on subsequent runs
- Progress tracking with ETA display

**Requirements:**
- **Images**: Pillow (install: `pip install Pillow`)
- **Videos**: FFmpeg (download from https://ffmpeg.org)
- **GPS/EXIF Metadata** (optional): ExifTool - automatically detected and used if available

**Example Output (with ExifTool):**
```
[20:49:29] Compositing 430 images...
[20:49:29] Metadata copying enabled (ExifTool detected, adds ~1.5s per image)
[20:49:29] [1/430 0.2%] OK 2025-10-16_194703_Image_9ce001ca.jpg | 0.6 img/s | ETA: 715s
[20:49:30] [2/430 0.5%] OK 2025-09-24_161956_Image_5b617512.jpg | 0.6 img/s | ETA: 713s
...
[20:59:44] Completed in 615.3s (1.43s per image)
[20:59:44] Images: 430 composited, 0 failed, 0 skipped
```

**Example Output (without ExifTool):**
```
[20:49:29] Compositing 430 images...
[20:49:29] Metadata copying disabled (ExifTool not found)
[20:49:29] [1/430 0.2%] OK 2025-10-16_194703_Image_9ce001ca.jpg | 10.2 img/s | ETA: 42s
[20:49:29] [2/430 0.5%] OK 2025-09-24_161956_Image_5b617512.jpg | 10.5 img/s | ETA: 41s
...
[20:50:11] Completed in 42.3s (0.10s per image)
[20:50:11] Images: 430 composited, 0 failed, 0 skipped
```

### Timezone Conversion

**NEW FEATURE:** The script now uses GPS coordinates to automatically determine the correct timezone for each memory!

By default, all files are downloaded with UTC timestamps (matching Snapchat's format). You can convert all timestamps and filenames to the timezone where the photo/video was actually taken.

**How it works:**
1. Reads UTC dates and GPS coordinates from `download_progress.json` for each file
2. Uses GPS coordinates to lookup the timezone where the memory was taken (e.g., 'America/New_York', 'Europe/Paris')
3. Falls back to system timezone for memories without GPS data
4. Renames files to use the determined timezone in filenames
5. Updates file modification/creation times to match
6. Tracks conversion status and current timezone in progress file
7. Preserves UTC dates in progress file for reference

**Requirements:**
- **GPS-based timezone lookup**: `timezonefinder` + `pytz` (install: `pip install timezonefinder pytz`)
- Without these libraries, the script falls back to system timezone (like before)

**Usage:**
```bash
python download_snapchat_memories.py --convert-timezone
```

**What gets converted:**
- All images in `memories/images/`
- All videos in `memories/videos/`
- All overlays in `memories/overlays/`
- All composited files in `memories/composited/images/` and `memories/composited/videos/`

**Example (with GPS-based timezone):**
```
Memory taken in New York (GPS: 40.7128, -74.0060):
- Before: `2025-10-16_194703_Image_9ce001ca.jpg` (UTC: 7:47 PM)
- After: `2025-10-16_144703_Image_9ce001ca.jpg` (EDT: 2:47 PM)

Memory taken in Los Angeles (GPS: 34.0522, -118.2437):
- Before: `2025-10-16_194703_Image_9ce001ca.jpg` (UTC: 7:47 PM)
- After: `2025-10-16_124703_Image_9ce001ca.jpg` (PDT: 12:47 PM)
```

**Example (without GPS data - fallback to system timezone):**
- Before: `2025-10-16_194703_Image_9ce001ca.jpg` (UTC: 7:47 PM)
- After: `2025-10-16_144703_Image_9ce001ca.jpg` (System timezone)

**Progress tracking:**
The `download_progress.json` file is updated to track:
- `timezone_converted`: Whether the file has been converted from UTC
- `current_timezone`: Which timezone the file is currently named in (e.g., 'UTC', 'America/New_York', or 'system')
- `local_date`: The date/time in the current timezone
- `location`: GPS coordinates (latitude, longitude) for GPS-based timezone lookup
- `date`: Original UTC date (always preserved for reference)

**Safety:**
- Safe to run multiple times - skips already converted files
- Original UTC dates always preserved in progress file
- GPS coordinates stored for future re-conversions if needed
- Can be undone by re-downloading files (they'll be UTC again)

### File Naming Convention

Files are named with the Snapchat creation timestamp and a short SID:

```
YYYY-MM-DD_HHMMSS_Type_sidXXXXXXXX.ext
```

**Format breakdown:**
- `YYYY-MM-DD`: Date with dashes for readability
- `HHMMSS`: Time (24-hour format, no colons to avoid filesystem issues)
- `Type`: "Image" or "Video" (capitalized)
- `sidXXXXXXXX`: First 8 characters of session ID (unique identifier)

**Examples:**
- `2025-10-16_194703_Image_9ce001ca.jpg` - Image taken Oct 16, 2025 at 19:47:03 UTC
- `2025-10-15_223151_Video_9f9eb970.mp4` - Video taken Oct 15, 2025 at 22:31:51 UTC
- `2025-10-16_194703_Image_9ce001ca_overlay.png` - Overlay/sticker for the image

### Resume Capability

If the download is interrupted:
1. The script saves progress to `download_progress.json` after each file
2. Re-running the script automatically skips already-downloaded files
3. Failed downloads are tracked and can be retried (up to 3 attempts)

### File Timestamp Preservation

The script sets file timestamps to match when the memory was created in Snapchat:

| Platform | Modification Time | Creation/Birth Time |
|----------|------------------|---------------------|
| **Linux** | ✅ Always set | ✅ Set automatically (kernel 3.5+, ext4/btrfs/xfs) |
| **macOS** | ✅ Always set | ✅ Set automatically (HFS+/APFS) |
| **Windows** | ✅ Always set | ⚠️ Requires `pywin32` (optional) |

This means sorting by date in your file browser will show chronological order based on when you took the photo/video in Snapchat, not when you downloaded it.

**Platform Details:**

- **Linux**: Uses built-in `os.utime()` with nanosecond precision - **no extra dependencies needed!**
- **macOS**: Birth time set automatically when files are created - **no extra dependencies needed!**
- **Windows**: Requires `pywin32` to set creation time:
  ```bash
  pip install pywin32
  ```

**TL;DR:** Linux and macOS are easier - they work out of the box without extra packages!

## Data Structure Analysis

### Snapchat Export Format

Each memory download link in the HTML:
```html
<a href="#" onclick="downloadMemories('https://...api.snapchat.com/dmd/mm?uid=...&sid=...&mid=...&ts=...&sig=...', this, true)">Download</a>
```

**URL Parameters:**
- `uid`: User ID
- `sid`: Session ID (unique per memory, used for naming)
- `mid`: Media ID
- `ts`: Timestamp
- `sig`: Signature for authentication

**Downloaded ZIP Contents:**
- `{sid}-main.jpg` or `{sid}-main.mp4` - The actual photo/video
- `{sid}-overlay.png` - Snapchat overlay/stickers/text

### HTML Table Structure

Each row contains:
1. **Date**: `YYYY-MM-DD HH:MM:SS UTC` format
2. **Media Type**: `Image` or `Video`
3. **Location**: GPS coordinates (latitude, longitude)
4. **Download Link**: JavaScript onclick with download URL

## Progress Tracking

The `download_progress.json` file structure:

```json
{
  "downloaded": {
    "9ce001ca-fa94-94c3-5514-8b5c7c118fb6": {
      "date": "2025-10-16 19:47:03 UTC",
      "media_type": "Image",
      "timestamp": "2025-10-19T02:30:15.123456"
    }
  },
  "failed": {
    "some-sid-that-failed": {
      "count": 2,
      "errors": [
        {
          "timestamp": "2025-10-19T02:25:10.123456",
          "error": "Connection timeout"
        }
      ]
    }
  }
}
```

## Verification

Check download status:
```bash
python download_snapchat_memories.py --verify
```

Output shows:
- Total memories found in HTML
- Number successfully downloaded
- Missing memories (not yet downloaded)
- Failed memories (with retry counts)

## Common Issues & Solutions

### Issue: "File is not a zip file" or Rate Limiting (HTTP 429)

**Problem:** Snapchat rate-limits download requests. If you download too fast, the server returns HTML error pages instead of ZIP files, causing "File is not a zip file" errors.

**Solution:**
1. The script now automatically detects rate limiting and retries with exponential backoff
2. Increase the delay between downloads:
   ```bash
   python download_snapchat_memories.py --delay 3.0  # 3 seconds between downloads
   # Or even slower:
   python download_snapchat_memories.py --delay 5.0  # 5 seconds
   ```
3. Failed downloads are tracked and will be automatically retried when you re-run
4. The script now retries rate-limited downloads up to 3 times with increasing wait times (5s, 10s, 20s)

### Issue: Files downloading with GUID names

**Solution:** The script handles this by:
1. Downloading to temporary ZIP files
2. Extracting contents
3. Renaming based on timestamp and SID
4. Deleting temporary files

### Issue: Need to track what's downloaded

**Solution:** The `download_progress.json` file tracks:
- Every successfully downloaded SID
- Failed downloads with error details
- Running the script again skips already-downloaded files

### Issue: Want to check if everything downloaded

**Solution:** Use verification mode:
```bash
python download_snapchat_memories.py --verify
```

### Issue: Some downloads failed

**Solution:**
1. Failed downloads are tracked in `download_progress.json`
2. The script will automatically retry them (up to 5 attempts)
3. Just run the script again to retry failures
4. If still failing due to rate limits, increase `--delay` parameter

### Issue: Files don't show chronological dates

**Solution:** The script sets file modification times to match Snapchat creation dates. Use "Date Modified" sorting in your file browser.

## Statistics

The script dynamically counts and reports:
- **Total Memories:** Parsed from your HTML export file
- **Date Range:** Based on your Snapchat usage history
- **Media Types:** Images and Videos with optional overlay files
- **Includes:** GPS location data for each memory

## Implementation Details

### Key Components

1. **MemoriesParser**: HTML parser to extract memory metadata
2. **SnapchatDownloader**: Main download and organization logic
3. **Progress Tracking**: JSON-based resume capability
4. **Verification**: Check download completeness

### Download Process

1. Parse HTML to extract all memory entries
2. For each memory:
   - Check if already downloaded (skip if yes)
   - Download ZIP file from Snapchat API
   - Extract main file and overlay
   - Rename based on timestamp + SID
   - Place in appropriate folder (images/videos/overlays)
   - Set file modification time
   - Update progress tracker
3. Report summary statistics

### Error Handling

- Network errors: Retry up to 3 times
- Invalid ZIP files: Skip and log error
- Missing metadata: Use fallback naming
- Progress saved after each successful download

## Recent Updates

### v1.3.0 - GPS-Based Timezone Conversion
- ✅ **NEW:** GPS-based timezone conversion using coordinates from each memory
- ✅ Automatically determines correct timezone (e.g., 'America/New_York') from GPS data
- ✅ Falls back to system timezone for memories without GPS coordinates
- ✅ Stores GPS coordinates and current timezone in progress file
- ✅ Requires `timezonefinder` + `pytz` libraries (optional, falls back gracefully)
- ✅ Files converted to the timezone where they were actually taken

### v1.2.0 - Timezone Conversion
- ✅ New `--convert-timezone` command to convert all files from UTC
- ✅ Converts both filenames and file timestamps
- ✅ Tracks conversion status in progress file
- ✅ Preserves original UTC dates for reference
- ✅ Safe to run multiple times (skips already converted files)

### v1.1.0 - Automatic Metadata Copying
- ✅ Metadata (GPS/EXIF) now automatically copied when ExifTool is available
- ✅ No manual flag needed - just install ExifTool and it works
- ✅ Removed `--copy-metadata` flag (feature is now automatic)

### v1.0.0 - Overlay Compositing Feature
- ✅ Added overlay compositing to recreate Snapchat's original look
- ✅ Fast processing: ~10 images/second without ExifTool
- ✅ Automatic metadata copying with ExifTool if installed
- ✅ Caching system for instant restarts (`overlay_pairs.json`)
- ✅ Progress tracking with real-time ETA
- ✅ Resumable: picks up where you left off if interrupted

## Future Enhancements

Potential improvements:
- Export location data to GPX/KML format
- Create photo gallery HTML viewer
- Organize by date folders (YYYY/MM/)
- Metadata CSV export
- Batch metadata operations

## Notes

**Download Features:**
- Uses a 2-second delay between downloads by default (increase with `--delay` if you encounter rate limiting)
- Handles both ZIP archives and direct media files (automatically detected using file signatures)
- Supports video formats: MP4, MOV, AVI, WebM, MKV
- Supports image formats: JPEG, PNG, GIF, TIFF
- File modification times are set to UTC (matching Snapchat's timestamp format)

**Overlay Compositing:**
- Overlays are matched to base files using filename patterns (same timestamp + SID)
- GPS/EXIF metadata automatically copied to composited files if ExifTool is available
- Composited files saved to separate `composited/` folder to preserve originals
- Cache file (`overlay_pairs.json`) speeds up subsequent runs
- High-quality JPEG output (quality=95) for composited images

**Data Handling:**
- Original GUIDs from Snapchat are not preserved (using SID instead)
- GPS location data automatically embedded in files when ExifTool is available
- Progress tracking in JSON format for easy inspection and debugging

## Author

Created with Claude Code for organizing Snapchat memories exports.
