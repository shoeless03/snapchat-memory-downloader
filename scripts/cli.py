#!/usr/bin/env python3
"""
Command-line interface for Snapchat Memories Downloader.
"""

import argparse
import sys
from snap_config import check_dependencies
from downloader import SnapchatDownloader

try:
    import questionary
    from questionary import Style
    MENU_AVAILABLE = True
except ImportError:
    MENU_AVAILABLE = False

# Custom style for the menu - Pastel Pink & Blue theme
# Colors designed to work on both black and white backgrounds
custom_style = Style([
    ('qmark', 'fg:#F48FB1 bold'),          # Question mark - Pastel Pink
    ('question', 'fg:#90CAF9 bold'),        # Question text - Pastel Blue
    ('answer', 'fg:#F48FB1 bold'),         # Selected answer - Pastel Pink
    ('pointer', 'fg:#F48FB1 bold'),        # Pointer symbol - Pastel Pink
    ('highlighted', 'fg:#90CAF9 bold'),    # Highlighted choice - Pastel Blue
    ('selected', 'fg:#F48FB1'),            # Selected choice - Pastel Pink
    ('separator', 'fg:#90CAF9'),           # Separator - Pastel Blue
    ('instruction', 'fg:#B39DDB'),         # Instruction text - Light Purple
    ('text', ''),                           # Plain text
    ('disabled', 'fg:#858585 italic')      # Disabled choices - Gray
])


def show_interactive_menu():
    """Show interactive menu for selecting operations."""
    if not MENU_AVAILABLE:
        print("Interactive menu not available (questionary not installed)")
        print("Install with: pip install questionary")
        return None

    print("\n" + "="*70)
    print("       /\\_/\\    Snapchat Memories Downloader    /\\_/\\")
    print("      ( o.o )        Interactive Menu          ( o.o )")
    print("       > ^ <                                    > ^ <")
    print("="*70)
    print("\nUse [UP]/[DOWN] arrow keys to navigate, [ENTER] to select\n")

    menu_options = [
        "[>>] Download memories from Snapchat export",
        "[+]  Apply overlays to images and videos",
        "[?]  Verify downloads",
        "[*]  Verify composited files",
        "[~]  Convert timezone (UTC -> Local)",
        "[X]  Exit"
    ]

    choice = questionary.select(
        "Select an operation:",
        choices=menu_options,
        style=custom_style
    ).ask()

    if choice is None or choice == "[X]  Exit":
        return None

    return menu_options.index(choice)


def get_submenu_choice(title, options):
    """Show a submenu for additional choices."""
    if not MENU_AVAILABLE:
        return 0

    print()
    choice = questionary.select(
        title,
        choices=options,
        style=custom_style
    ).ask()

    if choice is None:
        return 0

    return options.index(choice)


def run_operation(args, downloader):
    """Execute the selected operation based on args."""
    # Run timezone conversion
    if args.convert_timezone:
        print("Converting all files from UTC to local timezone...")
        downloader.convert_all_to_local_timezone()
        return

    # Run in composite overlay mode
    if args.apply_overlays:
        print("Compositing overlays onto base media files...")
        downloader.composite_all_overlays(
            images_only=args.images_only,
            videos_only=args.videos_only,
            rebuild_cache=args.rebuild_cache
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
        print(f"Failed composites: {results['failed']}")
        print(f"Missing composites: {results['missing']}")
        print(f"{'='*60}\n")

        if results['failed_list']:
            print("Failed composites:")
            for item in results['failed_list'][:10]:
                print(f"  - {item['file']} ({item['type']}, {item['attempts']} attempts)")
            if len(results['failed_list']) > 10:
                print(f"  ... and {len(results['failed_list']) - 10} more")
            print()

        if results['missing_list']:
            print("Missing composites (not yet attempted):")
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
    parser.add_argument('--convert-timezone', action='store_true',
                        help='Convert all file timestamps and filenames from UTC to local timezone')
    parser.add_argument('--interactive', action='store_true',
                        help='Show interactive menu')

    args = parser.parse_args()

    # Determine if we should show interactive menu
    # Show menu if --interactive flag OR if no action flags were provided
    show_menu = args.interactive or not any([
        args.verify,
        args.apply_overlays,
        args.verify_composites,
        args.convert_timezone
    ])

    # Check dependencies before starting
    check_dependencies()

    # Create downloader instance (once, reused for all operations)
    downloader = SnapchatDownloader(args.html, args.output)

    # Interactive menu loop
    if show_menu and MENU_AVAILABLE:
        while True:
            menu_choice = show_interactive_menu()

            if menu_choice is None:
                print("\nExiting...")
                return

            # Reset args for this iteration
            args.verify = False
            args.apply_overlays = False
            args.verify_composites = False
            args.convert_timezone = False
            args.images_only = False
            args.videos_only = False

            # Map menu choice to action
            if menu_choice == 0:  # Download
                pass  # Download will execute below
            elif menu_choice == 1:  # Apply overlays
                submenu = get_submenu_choice(
                    "[+] Apply overlays to:",
                    ["[*] Both images and videos", "[I] Images only", "[V] Videos only"]
                )
                args.apply_overlays = True
                if submenu == 1:
                    args.images_only = True
                elif submenu == 2:
                    args.videos_only = True
            elif menu_choice == 2:  # Verify downloads
                args.verify = True
            elif menu_choice == 3:  # Verify composites
                args.verify_composites = True
            elif menu_choice == 4:  # Convert timezone
                args.convert_timezone = True

            # Execute the operation
            run_operation(args, downloader)

            # After operation completes, loop back to menu
            print("\n" + "="*70)
            print("    *** Operation completed! /\\_/\\ Returning to menu... ***")
            print("="*70)

    else:
        # Command-line mode: run once and exit
        run_operation(args, downloader)


if __name__ == '__main__':
    main()
