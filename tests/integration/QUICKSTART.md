# Integration Test - Quick Start

Run a complete integration test in 3 steps:

## Option 1: Automated Test (Recommended)

```bash
cd tests/integration
python run_integration_test.py
```

This will:
1. Generate test files
2. Start test server
3. Download all 10 test memories
4. Verify downloads
5. Apply overlays
6. Stop server
7. Show results

**Expected time**: ~30-45 seconds

## Option 2: Manual Test

### Step 1: Generate test files
```bash
cd tests/integration
python create_test_files.py
```

### Step 2: Start server (keep this running)
```bash
python test_server.py
```

### Step 3: In a NEW terminal, run downloader
```bash
# From project root
python download_snapchat_memories.py \
  --html "tests/integration/data from snapchat/html/memories_history.html" \
  --output "tests/integration/memories"
```

### Step 4: Verify
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
```

### Step 5: Test overlays
```bash
python download_snapchat_memories.py \
  --html "tests/integration/data from snapchat/html/memories_history.html" \
  --output "tests/integration/memories" \
  --apply-overlays
```

Expected: 7 images + 2 videos composited

### Step 6: Stop server (Ctrl+C in server terminal)

## What Gets Created

After a successful test run:

```
tests/integration/memories/
├── images/              # 6 JPG files
├── videos/              # 4 MP4 files
├── overlays/            # 6 PNG files
└── composited/
    ├── images/          # 4 composited JPG files
    └── videos/          # 2 composited MP4 files
```

## Troubleshooting

**Server won't start**: Port 8000 already in use
- Solution: Change `PORT = 8000` to `PORT = 8001` in test_server.py

**No test files**: Need to generate them first
- Solution: Run `python create_test_files.py`

**Downloads fail**: Server not running
- Solution: Start server with `python test_server.py`

**Import errors**: Missing dependencies
- Solution: `pip install requests Pillow` (Pillow optional but recommended)

## Test Data Details

- **10 memories total**: 6 images, 4 videos
- **Covers**: ZIP files, direct downloads, overlays, GPS data, edge cases
- **Local only**: All URLs point to localhost:8000
- **Realistic**: Mimics actual Snapchat export structure

See [README.md](README.md) for detailed documentation.
