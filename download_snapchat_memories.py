#!/usr/bin/env python3
"""
Snapchat Memories Downloader

This script downloads all Snapchat memories from the HTML export file,
organizing them with proper timestamps and tracking progress.

Main entry point - imports and runs the CLI from the refactored modules.

Module Structure:
- cli.py: Command-line interface and main entry point
- config.py: Configuration and dependency checking
- parser.py: HTML parsing for memories_history.html
- downloader.py: Download orchestration and file handling
- metadata.py: File timestamps and GPS metadata operations
- compositor.py: Overlay compositing for images and videos
- progress.py: Progress tracking and verification

Usage:
    python download_snapchat_memories.py [options]

    Options:
        --html PATH              Path to memories_history.html
        --output PATH            Output directory for memories
        --delay SECONDS          Delay between downloads (default: 2.0)
        --verify                 Verify downloads without downloading
        --apply-overlays         Composite overlays onto media
        --images-only            Only composite images
        --videos-only            Only composite videos
        --verify-composites      Verify composited files
        --rebuild-cache          Rebuild overlay pairs cache
        --copy-metadata          Copy metadata (slow, adds ~1.5s per image)

Examples:
    # Download all memories
    python download_snapchat_memories.py

    # Verify what's been downloaded
    python download_snapchat_memories.py --verify

    # Apply overlays to create composited images/videos
    python download_snapchat_memories.py --apply-overlays

    # Apply overlays only to images (faster)
    python download_snapchat_memories.py --apply-overlays --images-only

For more information, see CLAUDE.md
"""

from cli import main


if __name__ == '__main__':
    main()
