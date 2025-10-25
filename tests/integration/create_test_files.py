#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create realistic test files for integration testing.
This script generates:
- Sample image files (JPG)
- Sample video files (MP4)
- Sample overlay files (PNG with transparency)
- ZIP archives containing main + overlay files
"""

import os
import sys
import zipfile
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: Pillow not installed. Install with: pip install Pillow")


def create_test_image(path: Path, width: int = 1920, height: int = 1080, text: str = "Test Image"):
    """Create a test JPEG image with text overlay."""
    if not HAS_PIL:
        print(f"Skipping {path} - Pillow not available")
        return False

    # Create a colorful gradient image
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    # Draw gradient background
    for y in range(height):
        color_value = int(255 * (y / height))
        draw.rectangle([(0, y), (width, y + 1)], fill=(color_value, 100, 255 - color_value))

    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text with shadow
    draw.text((x + 3, y + 3), text, fill=(0, 0, 0), font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    # Save as JPEG
    img.save(path, 'JPEG', quality=95)
    print(f"✓ Created {path}")
    return True


def create_test_overlay(path: Path, width: int = 1920, height: int = 1080, text: str = "🎉 Snap!"):
    """Create a test PNG overlay with transparency."""
    if not HAS_PIL:
        print(f"Skipping {path} - Pillow not available")
        return False

    # Create transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Add overlay text at top
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    # Draw text with semi-transparent background
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x = (width - text_width) // 2
    y = 50

    # Background rectangle
    padding = 20
    draw.rectangle(
        [(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)],
        fill=(0, 0, 0, 180)
    )

    # Text
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Add some decorative elements
    # Corner circles
    for corner_x, corner_y in [(100, 100), (width - 100, 100), (100, height - 100), (width - 100, height - 100)]:
        draw.ellipse([(corner_x - 30, corner_y - 30), (corner_x + 30, corner_y + 30)],
                     fill=(255, 200, 0, 200))

    # Save as PNG with transparency
    img.save(path, 'PNG')
    print(f"✓ Created {path}")
    return True


def create_test_video(path: Path, duration: int = 3):
    """Create a test MP4 video file.

    Note: This creates a minimal valid MP4 file structure.
    For real video generation, you'd need ffmpeg.
    """
    # Create a minimal valid MP4 file
    # This is a simplified MP4 structure that can be detected as video
    mp4_header = bytes([
        # ftyp box
        0x00, 0x00, 0x00, 0x20,  # box size
        0x66, 0x74, 0x79, 0x70,  # 'ftyp'
        0x69, 0x73, 0x6F, 0x6D,  # 'isom' major brand
        0x00, 0x00, 0x02, 0x00,  # minor version
        0x69, 0x73, 0x6F, 0x6D,  # compatible brands
        0x69, 0x73, 0x6F, 0x32,
        0x61, 0x76, 0x63, 0x31,
        0x6D, 0x70, 0x34, 0x31,

        # moov box (minimal)
        0x00, 0x00, 0x00, 0x28,  # box size
        0x6D, 0x6F, 0x6F, 0x76,  # 'moov'

        # mvhd box (movie header)
        0x00, 0x00, 0x00, 0x20,  # box size
        0x6D, 0x76, 0x68, 0x64,  # 'mvhd'
        0x00, 0x00, 0x00, 0x00,  # version + flags
        0x00, 0x00, 0x00, 0x00,  # creation time
        0x00, 0x00, 0x00, 0x00,  # modification time
        0x00, 0x00, 0x03, 0xE8,  # timescale (1000)
        0x00, 0x00, 0x0B, 0xB8,  # duration (3000 = 3 seconds)
    ])

    with open(path, 'wb') as f:
        f.write(mp4_header)
        # Add some padding to make it more realistic
        f.write(b'\x00' * 1024)

    print(f"✓ Created {path} (minimal MP4 structure)")
    return True


def create_zip_with_files(zip_path: Path, files: dict):
    """Create a ZIP file containing the specified files.

    Args:
        zip_path: Path to the output ZIP file
        files: Dict mapping archive names to file paths
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for archive_name, file_path in files.items():
            if file_path.exists():
                zipf.write(file_path, archive_name)
    print(f"✓ Created {zip_path}")


def main():
    """Create all test files."""
    # Base paths
    script_dir = Path(__file__).parent
    server_files = script_dir / "test_server_files"
    temp_dir = script_dir / "temp"

    # Create directories
    server_files.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)

    print("\n=== Creating Test Media Files ===\n")

    # Test 1: Image with overlay and GPS
    img1 = temp_dir / "abc12345-1111-2222-3333-444444444444-main.jpg"
    overlay1 = temp_dir / "abc12345-1111-2222-3333-444444444444-overlay.png"
    create_test_image(img1, text="NYC Sunset 🌆")
    create_test_overlay(overlay1, text="🗽 New York City")
    create_zip_with_files(
        server_files / "image1.zip",
        {
            "abc12345-1111-2222-3333-444444444444-main.jpg": img1,
            "abc12345-1111-2222-3333-444444444444-overlay.png": overlay1
        }
    )

    # Test 2: Image without overlay
    img2 = temp_dir / "def67890-4444-5555-6666-777777777777-main.jpg"
    create_test_image(img2, text="LA Beach 🏖️")
    create_zip_with_files(
        server_files / "image2.zip",
        {"def67890-4444-5555-6666-777777777777-main.jpg": img2}
    )

    # Test 3: Video with overlay
    vid1 = temp_dir / "ghi11223-7777-8888-9999-000000000000-main.mp4"
    overlay3 = temp_dir / "ghi11223-7777-8888-9999-000000000000-overlay.png"
    create_test_video(vid1)
    create_test_overlay(overlay3, text="🎥 London Calling")
    create_zip_with_files(
        server_files / "video1.zip",
        {
            "ghi11223-7777-8888-9999-000000000000-main.mp4": vid1,
            "ghi11223-7777-8888-9999-000000000000-overlay.png": overlay3
        }
    )

    # Test 4: Video without overlay
    vid2 = temp_dir / "jkl33445-aaaa-bbbb-cccc-dddddddddddd-main.mp4"
    create_test_video(vid2)
    create_zip_with_files(
        server_files / "video2.zip",
        {"jkl33445-aaaa-bbbb-cccc-dddddddddddd-main.mp4": vid2}
    )

    # Test 5: Direct JPG (not in ZIP)
    direct_img = server_files / "direct_image.jpg"
    create_test_image(direct_img, text="Paris 🗼")

    # Test 6: Direct MP4 (not in ZIP)
    direct_vid = server_files / "direct_video.mp4"
    create_test_video(direct_vid)

    # Test 7: Timezone conversion test
    img_tz = temp_dir / "stu99000-5555-6666-7777-888888888888-main.jpg"
    overlay_tz = temp_dir / "stu99000-5555-6666-7777-888888888888-overlay.png"
    create_test_image(img_tz, text="July 4th 🎆")
    create_test_overlay(overlay_tz, text="🇺🇸 Washington DC")
    create_zip_with_files(
        server_files / "image_timezone.zip",
        {
            "stu99000-5555-6666-7777-888888888888-main.jpg": img_tz,
            "stu99000-5555-6666-7777-888888888888-overlay.png": overlay_tz
        }
    )

    # Test 8: Special characters
    img_special = temp_dir / "vwx11222-9999-aaaa-bbbb-cccccccccccc-main.jpg"
    overlay_special = temp_dir / "vwx11222-9999-aaaa-bbbb-cccccccccccc-overlay.png"
    create_test_image(img_special, text="Sydney Opera 🎭")
    create_test_overlay(overlay_special, text="G'day Mate! 🦘")
    create_zip_with_files(
        server_files / "image_special.zip",
        {
            "vwx11222-9999-aaaa-bbbb-cccccccccccc-main.jpg": img_special,
            "vwx11222-9999-aaaa-bbbb-cccccccccccc-overlay.png": overlay_special
        }
    )

    # Test 9: Long video
    vid_long = temp_dir / "yzab3344-dddd-eeee-ffff-000000000000-main.mp4"
    overlay_long = temp_dir / "yzab3344-dddd-eeee-ffff-000000000000-overlay.png"
    create_test_video(vid_long, duration=10)
    create_test_overlay(overlay_long, text="🏛️ Rome")
    create_zip_with_files(
        server_files / "video_long.zip",
        {
            "yzab3344-dddd-eeee-ffff-000000000000-main.mp4": vid_long,
            "yzab3344-dddd-eeee-ffff-000000000000-overlay.png": overlay_long
        }
    )

    # Test 10: Old timestamp
    img_old = temp_dir / "cdef5566-1111-2222-3333-444444444444-main.jpg"
    overlay_old = temp_dir / "cdef5566-1111-2222-3333-444444444444-overlay.png"
    create_test_image(img_old, text="New Year 2020 🎉")
    create_test_overlay(overlay_old, text="🇷🇺 Moscow")
    create_zip_with_files(
        server_files / "image_old.zip",
        {
            "cdef5566-1111-2222-3333-444444444444-main.jpg": img_old,
            "cdef5566-1111-2222-3333-444444444444-overlay.png": overlay_old
        }
    )

    print("\n=== Summary ===")
    print(f"✓ Created {len(list(server_files.glob('*')))} test files in {server_files}")
    print(f"✓ Test data ready for integration testing")
    print(f"\nTo run tests:")
    print(f"  1. Start test server: python test_server.py")
    print(f"  2. Run downloader: python download_snapchat_memories.py --html \"tests/integration/data from snapchat/html/memories_history.html\" --output \"tests/integration/memories\"")

    # Clean up temp files
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n✓ Cleaned up temporary files")


if __name__ == "__main__":
    main()
