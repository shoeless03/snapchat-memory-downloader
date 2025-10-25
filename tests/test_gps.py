#!/usr/bin/env python3
"""Test GPS metadata on one file."""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from downloader import SnapchatDownloader

# Create downloader
dl = SnapchatDownloader('data from snapchat/html/memories_history.html', 'memories')

# Parse HTML
memories = dl.parse_html()

# Find first memory with location that's already downloaded
for memory in memories[:20]:
    sid = memory['sid']

    if sid not in dl.progress['downloaded']:
        continue

    if 'location' not in memory or not memory['location']:
        continue

    print(f"Testing with: {memory['date']} - {memory['media_type']}")
    print(f"Location: {memory['location']}")

    # Test parsing
    coords = dl._parse_location(memory)
    if coords:
        print(f"Parsed coordinates: {coords}")

        # Find the actual file
        for subdir in ['images', 'videos']:
            dir_path = Path('memories') / subdir
            if dir_path.exists():
                for file in dir_path.glob(f"*{sid[:8]}*"):
                    if 'overlay' not in file.name:
                        print(f"Found file: {file}")
                        print("Attempting to add GPS metadata...")

                        try:
                            dl._add_gps_metadata(file, memory)
                            print("[SUCCESS] GPS metadata added!")
                        except Exception as e:
                            print(f"[ERROR] {e}")

                        break
            break
    else:
        print("Failed to parse coordinates")

    break
