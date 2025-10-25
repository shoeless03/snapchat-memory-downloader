# Snapchat Memories Downloader

Download and organize your Snapchat memories from the "Download My Data" export.

## Quick Start

1. **Get your Snapchat data:**
   - Go to https://accounts.snapchat.com/accounts/downloadmydata
   - Request your data export
   - Download and extract the ZIP file when ready

2. **Run the downloader:**

   **Windows:**
   ```
   snapchat-memories-downloader.exe
   ```

   **macOS/Linux:**
   ```
   ./snapchat-memories-downloader
   ```

3. **Point to your HTML file:**
   ```
   snapchat-memories-downloader --html "path/to/memories_history.html"
   ```

## Features

- Downloads all your Snapchat memories (photos and videos)
- Preserves original timestamps
- Organizes files into `images/` and `videos/` folders
- Names files with dates and times (e.g., `2025-10-16_194703_Image.jpg`)
- Resumes interrupted downloads
- Applies Snapchat overlays back onto your images/videos

## Usage Examples

**Download all memories:**
```
snapchat-memories-downloader
```

**Custom HTML location:**
```
snapchat-memories-downloader --html "C:\Downloads\snapchat\memories_history.html"
```

**Verify what's been downloaded:**
```
snapchat-memories-downloader --verify
```

**Apply overlays to recreate original Snapchat look:**
```
snapchat-memories-downloader --apply-overlays
```

**Convert timestamps to your local timezone:**
```
snapchat-memories-downloader --convert-timezone
```

## Optional Enhancements

**For overlay compositing on videos:**
- Download FFmpeg from https://ffmpeg.org
- **Option A:** Add to your system PATH (recommended)
- **Option B:** Place `ffmpeg.exe` in the same folder as the downloader

**For GPS/EXIF metadata preservation:**
- Download ExifTool from https://exiftool.org
- **Option A:** Add to your system PATH (recommended)
- **Option B:** Place `exiftool.exe` in the same folder as the downloader

## Command-line Options

```
--html PATH          Path to memories_history.html
--output DIR         Output directory (default: memories)
--delay SECONDS      Delay between downloads (default: 2.0)
--verify             Check download status without downloading
--apply-overlays     Composite overlays onto images/videos
--images-only        Only process images when applying overlays
--videos-only        Only process videos when applying overlays
--verify-composites  Check which files have overlays applied
--convert-timezone   Convert all timestamps from UTC to local timezone
```

## Troubleshooting

**"File is not a zip file" errors:**
- Snapchat is rate-limiting you
- Increase delay: `--delay 5.0`
- The script will automatically retry failed downloads

**Downloads are slow:**
- This is normal - Snapchat rate-limits downloads
- Default 2-second delay prevents rate limiting
- Be patient - large exports can take hours

**Files show wrong dates:**
- Use `--convert-timezone` to convert from UTC to your local timezone
- File modification times will match when photos were taken

## Output Structure

```
memories/
├── images/              # Your photos
├── videos/              # Your videos
├── overlays/            # Snapchat stickers/text (if present)
└── composited/          # Images/videos with overlays applied
    ├── images/
    └── videos/
```

## Third-Party Software

This application uses the following open-source libraries:
- **requests** (Apache 2.0) - HTTP library
- **Pillow** (HPND) - Image processing
- **pywin32** (PSF, Windows only) - Windows file timestamp handling

See `licenses/` folder for full license texts.

## Support

For issues and updates, visit:
https://github.com/shoeless03/snapchat-memory-downloader

---

Built with PyInstaller | Powered by Python
