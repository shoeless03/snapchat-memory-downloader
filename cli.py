#!/usr/bin/env python3
"""
Command-line interface for Snapchat Memories Downloader.
"""

import argparse
from snap_config import check_dependencies
from downloader import SnapchatDownloader


def main():
    """Main entry point - parses arguments and orchestrates the download."""
    parser = argparse.ArgumentParser(description='Download Snapchat memories from HTML export')
    parser.add_argument('--html', default='data from snapchat/html/memories_history.html',
                        help='Path to memories_history.html file')
    parser.add_argument('--output', default='memories',
                        help='Output directory for downloaded memories')
    parser.add_argument('--delay', type=float, default=2.0,
                        help='Delay between downloads in seconds (default: 2.0, increase if rate limited)')
    parser.add_argument('--verify', action='store_true',
                        help='Verify downloads without downloading')
    parser.add_argument('--apply-overlays', action='store_true',
                        help='Composite overlay PNGs onto base images and videos')
    parser.add_argument('--images-only', action='store_true',
                        help='Only composite overlays onto images (skip videos)')
    parser.add_argument('--videos-only', action='store_true',
                        help='Only composite overlays onto videos (skip images)')
    parser.add_argument('--verify-composites', action='store_true',
                        help='Verify which files have been composited')
    parser.add_argument('--rebuild-cache', action='store_true',
                        help='Force rebuild of overlay pairs cache')
    parser.add_argument('--copy-metadata', action='store_true',
                        help='Copy EXIF/GPS metadata to composited files (slow, adds ~1.5s per image)')

    args = parser.parse_args()

    # Check dependencies before starting
    check_dependencies()

    # Create downloader instance
    downloader = SnapchatDownloader(args.html, args.output)

    # Run in composite overlay mode
    if args.apply_overlays:
        print("Compositing overlays onto base media files...")
        downloader.composite_all_overlays(
            images_only=args.images_only,
            videos_only=args.videos_only,
            rebuild_cache=args.rebuild_cache,
            copy_metadata=args.copy_metadata
        )
        return

    # Run in composite verification mode
    if args.verify_composites:
        print("Verifying composited files...")
        results = downloader.verify_composites()

        print(f"\nComposite Verification Results:")
        print(f"{'='*60}")
        print(f"Total overlay pairs: {results['total_pairs']}")
        print(f"Composited images: {results['composited_images']}")
        print(f"Composited videos: {results['composited_videos']}")
        print(f"Missing composites: {results['missing']}")
        print(f"{'='*60}\n")

        if results['missing_list']:
            print("Missing composites:")
            for item in results['missing_list'][:10]:
                print(f"  - {item}")
            if len(results['missing_list']) > 10:
                print(f"  ... and {len(results['missing_list']) - 10} more")
        return

    # Run in verification mode or download mode
    if args.verify:
        print("Verifying downloads...")
        results = downloader.verify_downloads()

        print(f"\nVerification Results:")
        print(f"{'='*60}")
        print(f"Total memories: {results['total']}")
        print(f"Downloaded: {results['downloaded']}")
        print(f"Missing: {len(results['missing'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"{'='*60}\n")

        if results['missing']:
            print("Missing memories:")
            for item in results['missing'][:10]:
                print(f"  - {item['date']} (SID: {item['sid'][:8]}...)")
            if len(results['missing']) > 10:
                print(f"  ... and {len(results['missing']) - 10} more")

        if results['failed']:
            print("\nFailed memories:")
            for item in results['failed'][:10]:
                print(f"  - {item['date']} (SID: {item['sid'][:8]}..., {item['attempts']} attempts)")
            if len(results['failed']) > 10:
                print(f"  ... and {len(results['failed']) - 10} more")
    else:
        # Download all memories
        downloader.download_all(delay=args.delay)


if __name__ == '__main__':
    main()
