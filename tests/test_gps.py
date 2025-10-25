#!/usr/bin/env python3
"""
Integration test for GPS metadata functionality.

This is a manual integration test that should be run with actual data.
It is skipped during automated test runs.
"""

import sys
from pathlib import Path
import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from metadata import parse_location, add_gps_metadata
from snap_parser import parse_html_file


@pytest.mark.skip(reason="Manual integration test - requires actual data files")
def test_gps_metadata_integration():
    """Manual integration test for GPS metadata.

    To run this test:
    1. Ensure you have actual memories downloaded
    2. Run with: pytest tests/test_gps.py -v -s
    """
    html_file = 'data from snapchat/html/memories_history.html'
    output_dir = Path('memories')

    if not Path(html_file).exists():
        pytest.skip("HTML file not found")

    # Parse HTML
    memories = parse_html_file(html_file)

    # Find first memory with location
    for memory in memories[:20]:
        sid = memory['sid']

        if 'location' not in memory or not memory['location']:
            continue

        print(f"\nTesting with: {memory['date']} - {memory['media_type']}")
        print(f"Location: {memory['location']}")

        # Test parsing
        coords = parse_location(memory)
        if coords:
            print(f"Parsed coordinates: {coords}")

            # Find the actual file
            for subdir in ['images', 'videos']:
                dir_path = output_dir / subdir
                if dir_path.exists():
                    for file in dir_path.glob(f"*{sid[:8]}*"):
                        if 'overlay' not in file.name:
                            print(f"Found file: {file}")
                            print("Attempting to add GPS metadata...")

                            try:
                                add_gps_metadata(file, memory, has_exiftool=True)
                                print("[SUCCESS] GPS metadata added!")
                            except Exception as e:
                                print(f"[ERROR] {e}")

                            break
                break
        else:
            print("Failed to parse coordinates")

        break


if __name__ == '__main__':
    # Allow running directly for manual testing
    test_gps_metadata_integration()
