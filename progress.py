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
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Validate structure
                    if not isinstance(data, dict):
                        raise ValueError("Progress file is not a JSON object")
                    return data
            except json.JSONDecodeError as e:
                print(f"\n{'='*70}")
                print(f"ERROR: Progress file is corrupted!")
                print(f"{'='*70}")
                print(f"File: {self.progress_file}")
                print(f"Error: {e}")
                print(f"\nThe progress file contains invalid JSON and cannot be loaded.")
                print(f"Please restore from backup or delete the file to start fresh.")
                print(f"{'='*70}\n")
                import sys
                sys.exit(1)
            except Exception as e:
                print(f"\n{'='*70}")
                print(f"ERROR: Failed to load progress file!")
                print(f"{'='*70}")
                print(f"File: {self.progress_file}")
                print(f"Error: {e}")
                print(f"\nCannot continue without a valid progress file.")
                print(f"{'='*70}\n")
                import sys
                sys.exit(1)
        return {
            'downloaded': {},
            'failed': {},
            'composited': {'images': {}, 'videos': {}},
            'failed_composites': {'images': {}, 'videos': {}}
        }

    def save_progress(self):
        """Save download progress to JSON file with backup and atomic write."""
        import shutil
        import tempfile

        # Create backup of existing file before saving
        backup_file = self.progress_file + '.backup'
        if os.path.exists(self.progress_file):
            try:
                shutil.copy2(self.progress_file, backup_file)
            except Exception as e:
                print(f"WARNING: Could not create backup: {e}")

        # Write to temporary file first (atomic write)
        temp_file = self.progress_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2)

            # Replace original file with temp file (atomic on most systems)
            if os.path.exists(self.progress_file):
                os.replace(temp_file, self.progress_file)
            else:
                os.rename(temp_file, self.progress_file)

        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            print(f"ERROR: Failed to save progress file: {e}")
            raise

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
            'date': memory['date'],  # Always UTC
            'media_type': memory['media_type'],
            'timestamp': datetime.now().isoformat(),
            'timezone_converted': False,  # Track if converted to local timezone
            'local_date': None  # Will be set when timezone is converted
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

        # Ensure both images and videos keys exist
        if 'images' not in self.progress['composited']:
            self.progress['composited']['images'] = {}
        if 'videos' not in self.progress['composited']:
            self.progress['composited']['videos'] = {}

        composited_dict = self.progress['composited']['images' if media_type == 'image' else 'videos']
        composited_dict[sid] = {
            'timestamp': datetime.now().isoformat(),
            'base_file': str(base_file),
            'overlay_file': str(overlay_file)
        }

        # Remove from failed composites if present
        if 'failed_composites' not in self.progress:
            self.progress['failed_composites'] = {'images': {}, 'videos': {}}

        failed_dict = self.progress['failed_composites']['images' if media_type == 'image' else 'videos']
        if sid in failed_dict:
            del failed_dict[sid]

        self.save_progress()

    def record_composite_failure(self, sid: str, media_type: str, base_file: str, overlay_file: str, error_msg: str):
        """Record a failed composite attempt.

        Args:
            sid: Session ID
            media_type: 'image' or 'video'
            base_file: Path to base file
            overlay_file: Path to overlay file
            error_msg: Error message
        """
        if 'failed_composites' not in self.progress:
            self.progress['failed_composites'] = {'images': {}, 'videos': {}}

        # Ensure both images and videos keys exist
        if 'images' not in self.progress['failed_composites']:
            self.progress['failed_composites']['images'] = {}
        if 'videos' not in self.progress['failed_composites']:
            self.progress['failed_composites']['videos'] = {}

        failed_dict = self.progress['failed_composites']['images' if media_type == 'image' else 'videos']

        if sid not in failed_dict:
            failed_dict[sid] = {
                'count': 0,
                'errors': [],
                'base_file': str(base_file),
                'overlay_file': str(overlay_file)
            }

        failed_dict[sid]['count'] += 1
        failed_dict[sid]['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        })
        self.save_progress()

    def get_composite_failure_count(self, sid: str, media_type: str) -> int:
        """Get the number of times a composite has failed.

        Args:
            sid: Session ID
            media_type: 'image' or 'video'

        Returns:
            Number of failed attempts
        """
        if 'failed_composites' not in self.progress:
            return 0

        failed_dict = self.progress['failed_composites'].get('images' if media_type == 'image' else 'videos', {})
        if sid in failed_dict:
            return failed_dict[sid].get('count', 0)
        return 0

    def is_timezone_converted(self, sid: str) -> bool:
        """Check if a file has been converted to local timezone.

        Args:
            sid: Session ID

        Returns:
            True if timezone has been converted
        """
        if sid in self.progress['downloaded']:
            return self.progress['downloaded'][sid].get('timezone_converted', False)
        return False

    def mark_timezone_converted(self, sid: str, local_date: str):
        """Mark a file as converted to local timezone.

        Args:
            sid: Session ID
            local_date: Date/time in local timezone (same format as UTC date)
        """
        if sid in self.progress['downloaded']:
            self.progress['downloaded'][sid]['timezone_converted'] = True
            self.progress['downloaded'][sid]['local_date'] = local_date
            self.save_progress()

    def get_utc_date(self, sid: str) -> str:
        """Get the UTC date for a SID.

        Args:
            sid: Session ID

        Returns:
            UTC date string or None
        """
        if sid in self.progress['downloaded']:
            return self.progress['downloaded'][sid].get('date')
        return None

    def get_local_date(self, sid: str) -> str:
        """Get the local timezone date for a SID.

        Args:
            sid: Session ID

        Returns:
            Local date string or None
        """
        if sid in self.progress['downloaded']:
            return self.progress['downloaded'][sid].get('local_date')
        return None

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
