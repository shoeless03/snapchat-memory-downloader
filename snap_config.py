"""
Configuration and dependency checking for Snapchat Memories Downloader.
"""

import sys
import platform
import shutil
from pathlib import Path


def check_exiftool() -> bool:
    """Check if ExifTool is available."""
    script_dir = Path(__file__).parent

    # Check different possible locations based on platform
    if platform.system() == 'Windows':
        exiftool_local = script_dir / 'exiftool-13.39_64' / 'exiftool(-k).exe'
    else:
        exiftool_local = script_dir / 'exiftool'

    return exiftool_local.exists() or shutil.which('exiftool') is not None


def check_pywin32() -> bool:
    """Check if pywin32 is available (Windows only)."""
    if platform.system() != 'Windows':
        return True  # Not needed on non-Windows platforms

    try:
        import pywintypes
        import win32file
        return True
    except ImportError:
        return False


def check_pillow() -> tuple[bool, bool]:
    """Check if Pillow is available.

    Returns:
        (has_pillow, has_pillow_simd)
    """
    has_pillow = True
    has_pillow_simd = False

    try:
        from PIL import Image
        # Check if it's pillow-simd
        try:
            has_pillow_simd = 'post' in Image.__version__ or 'simd' in Image.PILLOW_VERSION.lower()
        except:
            pass
    except ImportError:
        has_pillow = False

    return has_pillow, has_pillow_simd


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    return shutil.which('ffmpeg') is not None


def check_timezone_lookup() -> bool:
    """Check if timezone lookup libraries are available.

    Returns:
        True if both timezonefinder and pytz are installed
    """
    try:
        import timezonefinder
        import pytz
        return True
    except ImportError:
        return False


def check_dependencies():
    """Check for optional dependencies and prompt user."""
    has_exiftool = check_exiftool()
    has_pywin32 = check_pywin32()
    has_pillow, has_pillow_simd = check_pillow()
    has_ffmpeg = check_ffmpeg()
    has_timezone_lookup = check_timezone_lookup()

    # Display dependency status
    missing_features = []

    if not has_exiftool:
        missing_features.append(("ExifTool", "GPS metadata embedding"))

    if not has_pywin32 and platform.system() == 'Windows':
        missing_features.append(("pywin32", "setting file creation dates on Windows"))

    if not has_pillow:
        missing_features.append(("Pillow", "compositing overlays onto images"))

    if not has_ffmpeg:
        missing_features.append(("FFmpeg", "compositing overlays onto videos"))

    if not has_timezone_lookup:
        missing_features.append(("timezonefinder + pytz", "GPS-based timezone conversion"))

    if missing_features:
        print("\n" + "="*70)
        print("OPTIONAL DEPENDENCIES")
        print("="*70)
        print("\nThe following optional features are not available:\n")

        for dep, feature in missing_features:
            print(f"  • {dep}: Required for {feature}")

        print("\nInstallation instructions:")
        if not has_exiftool:
            print("\n  ExifTool:")
            print("    - Windows: Download from https://exiftool.org/")
            print("               Extract to this folder as 'exiftool-13.39_64/'")
            print("    - Linux:   sudo apt install libimage-exiftool-perl")
            print("    - macOS:   brew install exiftool")

        if not has_pywin32 and platform.system() == 'Windows':
            print("\n  pywin32:")
            print("    - Windows: pip install pywin32")

        if not has_pillow:
            print("\n  Pillow:")
            print("    - All platforms: pip install pillow-simd")
            print("      (pillow-simd is 5x faster than regular Pillow)")

        if not has_ffmpeg:
            print("\n  FFmpeg:")
            print("    - Windows: Download from https://ffmpeg.org/download.html")
            print("               Add to PATH or place ffmpeg.exe in this folder")
            print("    - Linux:   sudo apt install ffmpeg")
            print("    - macOS:   brew install ffmpeg")

        if not has_timezone_lookup:
            print("\n  Timezone Lookup (timezonefinder + pytz):")
            print("    - All platforms: pip install timezonefinder pytz")
            print("      (Required for GPS-based timezone conversion)")

        print("\nWhat would you like to do?")
        print("  1. Continue without these features")
        print("  2. Quit to install dependencies (recommended)")
        print("="*70)

        while True:
            try:
                choice = input("\nEnter your choice (1 or 2): ").strip()
                if choice == '1':
                    print("\nContinuing with available features...")
                    if not has_exiftool:
                        print("  - GPS metadata will NOT be added to files")
                    if not has_pywin32 and platform.system() == 'Windows':
                        print("  - File creation dates will NOT be set (modification dates will still work)")
                    if not has_pillow:
                        print("  - Image overlays will NOT be composited")
                    if not has_ffmpeg:
                        print("  - Video overlays will NOT be composited")
                    if not has_timezone_lookup:
                        print("  - GPS-based timezone conversion will NOT be available (falls back to system timezone)")
                    print("\nNOTE: You can install these dependencies later and re-run the script")
                    print("      to add GPS data, update timestamps, and composite overlays on your existing files.")
                    print()
                    break
                elif choice == '2':
                    print("\nExiting. Please install the dependencies and run the script again.")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please enter 1 or 2.")
            except (KeyboardInterrupt, EOFError):
                print("\n\nExiting...")
                sys.exit(0)
    else:
        print("\n" + "="*70)
        print("All optional dependencies found!")
        print("  [OK] ExifTool: GPS metadata will be embedded")
        if platform.system() == 'Windows':
            print("  [OK] pywin32: File creation dates will be set")
        if has_pillow_simd:
            print("  [OK] Pillow-SIMD: Image overlays can be composited (5x faster!)")
        else:
            print("  [OK] Pillow: Image overlays can be composited")
            print("  [TIP] For 5x faster compositing, install pillow-simd:")
            print("        pip uninstall Pillow && pip install pillow-simd")
        print("  [OK] FFmpeg: Video overlays can be composited")
        print("  [OK] Timezone Lookup: GPS-based timezone conversion available")
        print("="*70 + "\n")
