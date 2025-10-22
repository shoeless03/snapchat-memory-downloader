"""
HTML parser for Snapchat memories export file.
"""

import re
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs
from typing import List, Dict


class MemoriesParser(HTMLParser):
    """Parse the Snapchat memories HTML file to extract download links and metadata.

    The HTML contains a table with rows for each memory:
    - Date (YYYY-MM-DD HH:MM:SS UTC)
    - Media Type (Image/Video)
    - Location (Latitude, Longitude)
    - Download link (in onclick handler)
    """

    def __init__(self):
        super().__init__()
        self.memories = []
        self.current_row = {}
        self.current_tag = None
        self.td_count = 0
        self.in_table_row = False

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_table_row = True
            self.current_row = {}
            self.td_count = 0
        elif tag == 'td' and self.in_table_row:
            self.current_tag = 'td'
        elif tag == 'a' and self.in_table_row:
            attrs_dict = dict(attrs)
            onclick = attrs_dict.get('onclick', '')

            # Extract URL from onclick="downloadMemories('URL', this, true)"
            match = re.search(r"downloadMemories\('(.+?)',\s*this,\s*(true|false)\)", onclick)
            if match:
                self.current_row['download_url'] = match.group(1)

    def handle_data(self, data):
        if self.current_tag == 'td' and self.in_table_row:
            data = data.strip()
            if data and data not in ['Download', 'Downloaded']:
                if self.td_count == 0:  # Date column
                    self.current_row['date'] = data
                elif self.td_count == 1:  # Media Type column
                    self.current_row['media_type'] = data
                elif self.td_count == 2:  # Location column
                    self.current_row['location'] = data

    def handle_endtag(self, tag):
        if tag == 'td':
            self.td_count += 1
            self.current_tag = None
        elif tag == 'tr' and self.in_table_row:
            self.in_table_row = False
            if 'download_url' in self.current_row and 'date' in self.current_row:
                # Extract SID from URL for unique identification
                parsed = urlparse(self.current_row['download_url'])
                params = parse_qs(parsed.query)
                if 'sid' in params:
                    self.current_row['sid'] = params['sid'][0]
                    self.memories.append(self.current_row.copy())


def parse_html_file(html_file: str) -> List[Dict]:
    """Parse the HTML file and extract all memories.

    Args:
        html_file: Path to memories_history.html

    Returns:
        List of memory dictionaries with keys:
        - date: When the memory was created
        - media_type: 'Image' or 'Video'
        - location: GPS coordinates string
        - download_url: URL to download the memory
        - sid: Session ID (unique identifier)
    """
    print(f"Parsing {html_file}...")

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parser = MemoriesParser()
    parser.feed(html_content)

    print(f"Found {len(parser.memories)} memories to download")
    return parser.memories
