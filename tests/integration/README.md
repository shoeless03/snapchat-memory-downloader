# Integration Test Data

This folder contains a complete integration test setup for the Snapchat Memories Downloader.

## Structure

```
tests/integration/
├── data from snapchat/          # Mimics real Snapchat export structure
│   └── html/
│       └── memories_history.html   # Test HTML with 10 sample memories
│
├── test_server_files/           # Files served by test HTTP server
│   ├── image1.zip              # Image with overlay (NYC)
│   ├── image2.zip              # Image without overlay (LA)
│   ├── video1.zip              # Video with overlay (London)
│   ├── video2.zip              # Video without overlay
│   ├── direct_image.jpg        # Direct JPG file (Paris)
│   ├── direct_video.mp4        # Direct MP4 file (Tokyo)
│   ├── image_timezone.zip      # For timezone testing (DC)
│   ├── image_special.zip       # Special characters (Sydney)
│   ├── video_long.zip          # Long video (Rome)
│   └── image_old.zip           # Old timestamp 2020 (Moscow)
│
├── create_test_files.py        # Script to generate test media
├── test_server.py              # HTTP server for serving files
└── README.md                   # This file
```

## Test Data Coverage

The test dataset includes 10 memories covering various scenarios:

| # | Type  | Overlay | GPS | Special Feature | Location |
|---|-------|---------|-----|-----------------|----------|
| 1 | Image | ✓ | ✓ | Standard case | NYC |
| 2 | Image | ✗ | ✓ | No overlay | LA |
| 3 | Video | ✓ | ✓ | Standard video | London |
| 4 | Video | ✗ | ✗ | No GPS data | Unknown |
| 5 | Image | ✗ | ✓ | Direct JPG (not ZIP) | Paris |
| 6 | Video | ✗ | ✓ | Direct MP4 (not ZIP) | Tokyo |
| 7 | Image | ✓ | ✓ | Timezone conversion | DC |
| 8 | Image | ✓ | ✓ | Special characters | Sydney |
| 9 | Video | ✓ | ✓ | Long video | Rome |
| 10 | Image | ✓ | ✓ | Old timestamp (2020) | Moscow |

## Usage

### 1. Generate Test Files

First, create the test media files and ZIP archives:

```bash
cd tests/integration
python create_test_files.py
```

This creates:
- Sample JPG images with colorful gradients and text
- Sample PNG overlays with transparency and decorative elements
- Minimal valid MP4 video files
- ZIP archives containing main + overlay files

**Requirements:**
- Python 3.11+
- Pillow (optional but recommended): `pip install Pillow`
  - Without Pillow, placeholder files will be created

### 2. Start Test Server

Run the HTTP server to serve test files:

```bash
cd tests/integration
python test_server.py
```

The server will:
- Listen on `http://localhost:8000`
- Serve files from `test_server_files/` directory
- Log all download requests with timestamps
- Add CORS headers for local testing

**Server Output:**
```
============================================================
Snapchat Memories Integration Test Server
============================================================
Server directory: \\nas\data\media\photos\snap2\tests\integration\test_server_files
Files available:  10
Listening on:     http://localhost:8000
============================================================

Test files available:
  • direct_image.jpg             (XXX,XXX bytes)
  • direct_video.mp4             (XXX bytes)
  • image1.zip                   (XXX,XXX bytes)
  ...

============================================================
Server started. Press Ctrl+C to stop.
============================================================
```

### 3. Run Downloader

In a **separate terminal**, run the downloader with test data:

```bash
# From project root
python download_snapchat_memories.py \
  --html "tests/integration/data from snapchat/html/memories_history.html" \
  --output "tests/integration/memories"
```

### 4. Verify Downloads

Check that all files were downloaded:

```bash
python download_snapchat_memories.py \
  --html "tests/integration/data from snapchat/html/memories_history.html" \
  --output "tests/integration/memories" \
  --verify
```

Expected output:
```
Total memories: 10
Downloaded: 10
Missing: 0
Failed: 0

✓ All memories downloaded successfully!
```

### 5. Test Overlay Compositing

Apply overlays to create composited files:

```bash
python download_snapchat_memories.py \
  --html "tests/integration/data from snapchat/html/memories_history.html" \
  --output "tests/integration/memories" \
  --apply-overlays
```

This should composite:
- 7 images with overlays
- 2 videos with overlays

### 6. Test Timezone Conversion

Convert timestamps from UTC to local timezone:

```bash
python download_snapchat_memories.py \
  --html "tests/integration/data from snapchat/html/memories_history.html" \
  --output "tests/integration/memories" \
  --convert-timezone
```

## Test Scenarios

### Basic Download Tests

1. **Standard ZIP files**: Most files are ZIP archives containing main + overlay
2. **Direct media files**: Tests direct JPG/MP4 downloads without ZIP wrapper
3. **Missing overlays**: Some files have no overlay (only main file in ZIP)
4. **Resume capability**: Stop downloader mid-run and restart to test progress tracking

### Advanced Feature Tests

1. **Overlay Compositing**:
   - Images with overlays (7 files)
   - Videos with overlays (2 files)
   - Skipping files without overlays
   - Metadata preservation (if ExifTool installed)

2. **Timezone Conversion**:
   - Convert all timestamps from UTC to local time
   - Rename files with local timestamps
   - Track conversion status in progress file

3. **GPS Data**:
   - 9 out of 10 files have GPS coordinates
   - Test metadata embedding (requires ExifTool)

4. **Edge Cases**:
   - Old timestamps (year 2020)
   - Special characters in overlays
   - Empty location fields
   - Various media formats

### Performance Tests

- Download 10 files with 2-second delay (~25 seconds total)
- Composite 7 images + 2 videos
- Verify all downloads complete successfully
- Check progress tracking accuracy

## Expected Output Structure

After running all tests, you should have:

```
tests/integration/memories/
├── images/
│   ├── 2024-01-15_143045_Image_abc12345.jpg
│   ├── 2024-02-20_091530_Image_def67890.jpg
│   ├── 2024-05-12_112033_Image_mno55667.jpg
│   ├── 2024-07-04_000000_Image_stu99000.jpg
│   ├── 2024-08-22_131415_Image_vwx11222.jpg
│   └── 2020-01-01_000001_Image_cdef5566.jpg
│
├── videos/
│   ├── 2024-03-10_184512_Video_ghi11223.mp4
│   ├── 2024-04-05_220000_Video_jkl33445.mp4
│   ├── 2024-06-18_165520_Video_pqr77889.mp4
│   └── 2024-09-30_203045_Video_yzab3344.mp4
│
├── overlays/
│   ├── 2024-01-15_143045_Image_abc12345_overlay.png
│   ├── 2024-03-10_184512_Video_ghi11223_overlay.png
│   ├── 2024-07-04_000000_Image_stu99000_overlay.png
│   ├── 2024-08-22_131415_Image_vwx11222_overlay.png
│   ├── 2024-09-30_203045_Video_yzab3344_overlay.png
│   └── 2020-01-01_000001_Image_cdef5566_overlay.png
│
└── composited/
    ├── images/
    │   ├── 2024-01-15_143045_Image_abc12345_composited.jpg
    │   ├── 2024-07-04_000000_Image_stu99000_composited.jpg
    │   ├── 2024-08-22_131415_Image_vwx11222_composited.jpg
    │   └── 2020-01-01_000001_Image_cdef5566_composited.jpg
    │
    └── videos/
        ├── 2024-03-10_184512_Video_ghi11223_composited.mp4
        └── 2024-09-30_203045_Video_yzab3344_composited.mp4
```

## URL Structure

All URLs in the test HTML follow this pattern:

```
http://localhost:8000/test_server_files/{filename}?uid={user_id}&sid={session_id}&mid={media_id}&ts={timestamp}&sig={signature}
```

Example:
```
http://localhost:8000/test_server_files/image1.zip?uid=test_user_123&sid=abc12345-1111-2222-3333-444444444444&mid=m001&ts=1705330245&sig=test_sig_001
```

The SID (session ID) is used to:
- Uniquely identify each memory
- Generate consistent filenames
- Track download progress
- Match overlays to base files

## Troubleshooting

### Server won't start

**Problem**: `OSError: [Errno 98] Address already in use` (or 10048 on Windows)

**Solution**: Port 8000 is already in use. Either:
- Stop the other process using port 8000
- Edit `test_server.py` and change `PORT = 8000` to another port (e.g., 8001)
- Update HTML file URLs to match new port

### Test files not created

**Problem**: `create_test_files.py` fails or creates empty files

**Solution**:
- Install Pillow: `pip install Pillow`
- Check write permissions in `tests/integration/` directory
- Check available disk space

### Downloads fail

**Problem**: Downloader can't connect to test server

**Solution**:
- Verify test server is running: `http://localhost:8000` in browser
- Check firewall isn't blocking localhost connections
- Ensure HTML path is correct: `tests/integration/data from snapchat/html/memories_history.html`

### Compositing fails

**Problem**: `--apply-overlays` doesn't work

**Solution**:
- For images: Install Pillow: `pip install Pillow`
- For videos: Install FFmpeg: https://ffmpeg.org
- Run `--verify` first to ensure all files downloaded

## Cleanup

To reset the test environment:

```bash
# Remove downloaded files
rm -rf tests/integration/memories/

# Remove test server files (will need to regenerate)
rm -rf tests/integration/test_server_files/

# Remove progress tracking
rm -f tests/integration/download_progress.json
rm -f tests/integration/overlay_pairs.json
```

Then regenerate test files:
```bash
python tests/integration/create_test_files.py
```

## Integration with CI/CD

You can use this setup for automated testing:

```bash
#!/bin/bash
# integration_test.sh

cd tests/integration

# 1. Generate test files
python create_test_files.py || exit 1

# 2. Start server in background
python test_server.py &
SERVER_PID=$!
sleep 2  # Wait for server to start

# 3. Run downloader
python ../../download_snapchat_memories.py \
  --html "data from snapchat/html/memories_history.html" \
  --output "memories" \
  --delay 0.5

# 4. Verify downloads
python ../../download_snapchat_memories.py \
  --html "data from snapchat/html/memories_history.html" \
  --output "memories" \
  --verify || { kill $SERVER_PID; exit 1; }

# 5. Test compositing
python ../../download_snapchat_memories.py \
  --html "data from snapchat/html/memories_history.html" \
  --output "memories" \
  --apply-overlays || { kill $SERVER_PID; exit 1; }

# 6. Cleanup
kill $SERVER_PID
echo "✓ All integration tests passed!"
```

## Notes

- Test data is deterministic - same files every time
- URLs point to localhost - no external dependencies
- Safe to commit to version control (small test files)
- Server logs all requests for debugging
- Progress tracking works identically to production use

## Credits

Created for testing the Snapchat Memories Downloader project.
