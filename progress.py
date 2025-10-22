"""
Progress tracking and verification for Snapchat memories downloads.
"""

import json
import os
from typing import Dict, List
from datetime import datetime


class ProgressTracker:
    """Track download progress and failed attempts."""

    def __init__(self, progress_file: str = "download_progress.json"):
        """Initialize progress tracker.

        Args:
            progress_file: Path to JSON file for storing progress
        """
        self.progress_file = progress_file
        self.progress = self._load_progress()

    def _load_progress(self) -> Dict:
        """Load download progress from JSON file."""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'downloaded': {}, 'failed': {}, 'composited': {'images': {}, 'videos': {}}}

    def save_progress(self):
        """Save download progress to JSON file."""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def is_downloaded(self, sid: str) -> bool:
        """Check if a memory has been downloaded.

        Args:
            sid: Session ID to check

        Returns:
            True if already downloaded
        """
        return sid in self.progress['downloaded']

    def mark_downloaded(self, sid: str, memory: Dict):
        """Mark a memory as successfully downloaded.

        Args:
            sid: Session ID
            memory: Memory dictionary with date and media_type
        """
        self.progress['downloaded'][sid] = {
            'date': memory['date'],
            'media_type': memory['media_type'],
            'timestamp': datetime.now().isoformat()
        }

        # Remove from failed list if present
        if sid in self.progress['failed']:
            del self.progress['failed'][sid]

        self.save_progress()

    def record_failure(self, sid: str, memory: Dict, error_msg: str, exception: Exception = None):
        """Record a failed download attempt.

        Args:
            sid: Session ID
            memory: Memory dictionary
            error_msg: Error message
            exception: Optional exception object
        """
        if sid not in self.progress['failed']:
            self.progress['failed'][sid] = {
                'count': 0,
                'errors': [],
                'url': memory['download_url']
            }

        self.progress['failed'][sid]['count'] += 1
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        }
        if exception:
            error_record['error_type'] = type(exception).__name__

        self.progress['failed'][sid]['errors'].append(error_record)
        self.save_progress()

    def get_failure_count(self, sid: str) -> int:
        """Get the number of times a download has failed.

        Args:
            sid: Session ID

        Returns:
            Number of failed attempts
        """
        if sid in self.progress['failed']:
            return self.progress['failed'][sid].get('count', 0)
        return 0

    def is_composited(self, sid: str, media_type: str) -> bool:
        """Check if a file has been composited.

        Args:
            sid: Session ID
            media_type: 'image' or 'video'

        Returns:
            True if already composited
        """
        if 'composited' not in self.progress:
            self.progress['composited'] = {'images': {}, 'videos': {}}

        composited_dict = self.progress['composited'].get('images' if media_type == 'image' else 'videos', {})
        return sid in composited_dict

    def mark_composited(self, sid: str, media_type: str, base_file: str, overlay_file: str):
        """Mark a file as composited.

        Args:
            sid: Session ID
            media_type: 'image' or 'video'
            base_file: Path to base file
            overlay_file: Path to overlay file
        """
        if 'composited' not in self.progress:
            self.progress['composited'] = {'images': {}, 'videos': {}}

        composited_dict = self.progress['composited']['images' if media_type == 'image' else 'videos']
        composited_dict[sid] = {
            'timestamp': datetime.now().isoformat(),
            'base_file': str(base_file),
            'overlay_file': str(overlay_file)
        }
        self.save_progress()

    def verify_downloads(self, memories: List[Dict]) -> Dict:
        """Verify all downloads are complete.

        Args:
            memories: List of memory dictionaries from HTML parser

        Returns:
            Dictionary with verification results:
            - total: Total number of memories
            - downloaded: Number successfully downloaded
            - missing: List of missing memories
            - failed: List of failed memories with attempt counts
        """
        results = {
            'total': len(memories),
            'downloaded': 0,
            'missing': [],
            'failed': []
        }

        for memory in memories:
            sid = memory['sid']
            if sid in self.progress['downloaded']:
                results['downloaded'] += 1
            elif sid in self.progress['failed']:
                results['failed'].append({
                    'sid': sid,
                    'date': memory['date'],
                    'attempts': self.progress['failed'][sid]['count']
                })
            else:
                results['missing'].append({
                    'sid': sid,
                    'date': memory['date']
                })

        return results
