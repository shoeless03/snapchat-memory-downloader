#!/usr/bin/env python3
"""
Snapchat Memories Downloader - Main Entry Point

This is the main entry point for the Snapchat Memories Downloader.
It simply delegates to the actual implementation in the scripts/ folder.

For documentation and usage, see docs/CLAUDE.md or docs/README.md
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from cli import main


if __name__ == '__main__':
    main()
