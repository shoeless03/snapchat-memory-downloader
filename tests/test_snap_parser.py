"""
Unit tests for snap_parser module.
"""

import sys
from pathlib import Path
import pytest
from io import StringIO

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from snap_parser import MemoriesParser, parse_html_file


class TestMemoriesParser:
    """Test the HTML parser for Snapchat memories."""

    def test_parser_initialization(self):
        """Test parser initializes with empty state."""
        parser = MemoriesParser()
        assert parser.memories == []
        assert parser.current_row == {}
        assert parser.current_tag is None
        assert parser.td_count == 0
        assert parser.in_table_row is False

    def test_parse_simple_table_row(self):
        """Test parsing a simple table row with all fields."""
        html = """
        <table>
            <tr>
                <td>2023-01-15 14:30:00 UTC</td>
                <td>Image</td>
                <td>Latitude, Longitude: 42.438072, -82.91975</td>
                <td><a onclick="downloadMemories('https://example.com/download?sid=abc123def456', this, true)">Download</a></td>
            </tr>
        </table>
        """
        parser = MemoriesParser()
        parser.feed(html)

        assert len(parser.memories) == 1
        memory = parser.memories[0]
        assert memory['date'] == '2023-01-15 14:30:00 UTC'
        assert memory['media_type'] == 'Image'
        assert memory['location'] == 'Latitude, Longitude: 42.438072, -82.91975'
        assert 'sid=abc123def456' in memory['download_url']
        assert memory['sid'] == 'abc123def456'

    def test_parse_video_type(self):
        """Test parsing a video memory."""
        html = """
        <tr>
            <td>2023-02-20 09:15:30 UTC</td>
            <td>Video</td>
            <td></td>
            <td><a onclick="downloadMemories('https://example.com/download?sid=xyz789', this, false)">Download</a></td>
        </tr>
        """
        parser = MemoriesParser()
        parser.feed(html)

        assert len(parser.memories) == 1
        assert parser.memories[0]['media_type'] == 'Video'
        assert parser.memories[0]['sid'] == 'xyz789'

    def test_parse_without_location(self):
        """Test parsing memory without GPS location."""
        html = """
        <tr>
            <td>2023-03-10 18:45:00 UTC</td>
            <td>Image</td>
            <td></td>
            <td><a onclick="downloadMemories('https://example.com/download?sid=test123', this, true)">Download</a></td>
        </tr>
        """
        parser = MemoriesParser()
        parser.feed(html)

        assert len(parser.memories) == 1
        memory = parser.memories[0]
        assert memory.get('location', '') == ''

    def test_parse_multiple_rows(self):
        """Test parsing multiple table rows."""
        html = """
        <table>
            <tr>
                <td>2023-01-15 14:30:00 UTC</td>
                <td>Image</td>
                <td>Latitude, Longitude: 42.438072, -82.91975</td>
                <td><a onclick="downloadMemories('https://example.com/download?sid=sid001', this, true)">Download</a></td>
            </tr>
            <tr>
                <td>2023-01-16 10:20:00 UTC</td>
                <td>Video</td>
                <td></td>
                <td><a onclick="downloadMemories('https://example.com/download?sid=sid002', this, true)">Download</a></td>
            </tr>
            <tr>
                <td>2023-01-17 16:00:00 UTC</td>
                <td>Image</td>
                <td>Latitude, Longitude: 40.7128, -74.0060</td>
                <td><a onclick="downloadMemories('https://example.com/download?sid=sid003', this, false)">Download</a></td>
            </tr>
        </table>
        """
        parser = MemoriesParser()
        parser.feed(html)

        assert len(parser.memories) == 3
        assert parser.memories[0]['sid'] == 'sid001'
        assert parser.memories[1]['sid'] == 'sid002'
        assert parser.memories[2]['sid'] == 'sid003'

    def test_skip_downloaded_text(self):
        """Test that 'Download' and 'Downloaded' text in cells is ignored."""
        html = """
        <tr>
            <td>2023-01-15 14:30:00 UTC</td>
            <td>Image</td>
            <td>Downloaded</td>
            <td><a onclick="downloadMemories('https://example.com/download?sid=test123', this, true)">Download</a></td>
        </tr>
        """
        parser = MemoriesParser()
        parser.feed(html)

        # Should still parse the row, just ignore the "Downloaded" text
        assert len(parser.memories) == 1

    def test_skip_row_without_download_link(self):
        """Test that rows without download links are skipped."""
        html = """
        <tr>
            <td>2023-01-15 14:30:00 UTC</td>
            <td>Image</td>
            <td></td>
            <td>No link here</td>
        </tr>
        """
        parser = MemoriesParser()
        parser.feed(html)

        assert len(parser.memories) == 0

    def test_skip_row_without_date(self):
        """Test that rows without dates are skipped."""
        html = """
        <tr>
            <td></td>
            <td>Image</td>
            <td></td>
            <td><a onclick="downloadMemories('https://example.com/download?sid=test123', this, true)">Download</a></td>
        </tr>
        """
        parser = MemoriesParser()
        parser.feed(html)

        assert len(parser.memories) == 0

    def test_extract_sid_from_url(self):
        """Test extracting SID from various URL formats."""
        test_cases = [
            ("downloadMemories('https://example.com/download?sid=abc123', this, true)", "abc123"),
            ("downloadMemories('https://example.com?sid=xyz789&other=param', this, false)", "xyz789"),
        ]

        for onclick, expected_sid in test_cases:
            html = f"""
            <tr>
                <td>2023-01-15 14:30:00 UTC</td>
                <td>Image</td>
                <td></td>
                <td><a onclick="{onclick}">Download</a></td>
            </tr>
            """
            parser = MemoriesParser()
            parser.feed(html)

            assert len(parser.memories) == 1
            assert parser.memories[0]['sid'] == expected_sid

    def test_parse_html_with_extra_content(self):
        """Test parsing HTML with extra content outside table."""
        html = """
        <html>
        <head><title>Memories</title></head>
        <body>
            <h1>Your Memories</h1>
            <p>Some intro text</p>
            <table>
                <thead>
                    <tr><th>Date</th><th>Type</th><th>Location</th><th>Action</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>2023-01-15 14:30:00 UTC</td>
                        <td>Image</td>
                        <td></td>
                        <td><a onclick="downloadMemories('https://example.com/download?sid=test123', this, true)">Download</a></td>
                    </tr>
                </tbody>
            </table>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        parser = MemoriesParser()
        parser.feed(html)

        assert len(parser.memories) == 1
        assert parser.memories[0]['sid'] == 'test123'


class TestParseHtmlFile:
    """Test the parse_html_file function."""

    def test_parse_html_file_not_found(self, tmp_path):
        """Test error when HTML file doesn't exist."""
        non_existent_file = tmp_path / "nonexistent.html"

        with pytest.raises(FileNotFoundError):
            parse_html_file(str(non_existent_file))

    def test_parse_html_file_success(self, tmp_path, capsys):
        """Test successful parsing of HTML file."""
        html_file = tmp_path / "memories.html"
        html_content = """
        <table>
            <tr>
                <td>2023-01-15 14:30:00 UTC</td>
                <td>Image</td>
                <td>Latitude, Longitude: 42.438072, -82.91975</td>
                <td><a onclick="downloadMemories('https://example.com/download?sid=test123', this, true)">Download</a></td>
            </tr>
            <tr>
                <td>2023-01-16 10:20:00 UTC</td>
                <td>Video</td>
                <td></td>
                <td><a onclick="downloadMemories('https://example.com/download?sid=test456', this, true)">Download</a></td>
            </tr>
        </table>
        """
        html_file.write_text(html_content, encoding='utf-8')

        memories = parse_html_file(str(html_file))

        assert len(memories) == 2
        assert memories[0]['sid'] == 'test123'
        assert memories[1]['sid'] == 'test456'

        # Check that it printed the count
        captured = capsys.readouterr()
        assert "Found 2 memories" in captured.out

    def test_parse_html_file_empty(self, tmp_path, capsys):
        """Test parsing an HTML file with no memories."""
        html_file = tmp_path / "empty.html"
        html_content = """
        <html>
        <body>
            <p>No memories found</p>
        </body>
        </html>
        """
        html_file.write_text(html_content, encoding='utf-8')

        memories = parse_html_file(str(html_file))

        assert len(memories) == 0
        captured = capsys.readouterr()
        assert "Found 0 memories" in captured.out

    def test_parse_html_file_encoding(self, tmp_path):
        """Test parsing HTML file with special characters."""
        html_file = tmp_path / "memories_utf8.html"
        html_content = """
        <table>
            <tr>
                <td>2023-01-15 14:30:00 UTC</td>
                <td>Image</td>
                <td>Café ☕</td>
                <td><a onclick="downloadMemories('https://example.com/download?sid=café123', this, true)">Download</a></td>
            </tr>
        </table>
        """
        html_file.write_text(html_content, encoding='utf-8')

        memories = parse_html_file(str(html_file))

        assert len(memories) == 1
        assert memories[0]['sid'] == 'café123'
