#!/usr/bin/env python3
"""
Simple HTTP server for integration testing.
Serves test files from test_server_files/ directory on localhost:8000
"""

import http.server
import socketserver
import os
from pathlib import Path


class TestServerHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves files from test_server_files directory."""

    def __init__(self, *args, **kwargs):
        # Change to test_server_files directory
        server_dir = Path(__file__).parent / "test_server_files"
        os.chdir(server_dir)
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Custom log format to show what's being requested."""
        # Extract just the filename from the path
        if args:
            path = args[0].split('?')[0]  # Remove query parameters
            filename = path.split('/')[-1]
            print(f"[{self.log_date_time_string()}] GET {filename} -> {args[1]}")
        else:
            super().log_message(format, *args)

    def end_headers(self):
        """Add CORS headers to allow local testing."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()


def main():
    """Start the test server."""
    PORT = 8000
    server_dir = Path(__file__).parent / "test_server_files"

    # Verify server directory exists
    if not server_dir.exists():
        print(f"Error: {server_dir} does not exist!")
        print("Run 'python create_test_files.py' first to create test files.")
        return

    file_count = len(list(server_dir.glob('*')))
    print("=" * 60)
    print("Snapchat Memories Integration Test Server")
    print("=" * 60)
    print(f"Server directory: {server_dir}")
    print(f"Files available:  {file_count}")
    print(f"Listening on:     http://localhost:{PORT}")
    print("=" * 60)
    print("\nTest files available:")
    for f in sorted(server_dir.glob('*')):
        size = f.stat().st_size
        print(f"  • {f.name:30s} ({size:,} bytes)")
    print("\n" + "=" * 60)
    print("Server started. Press Ctrl+C to stop.")
    print("=" * 60 + "\n")

    # Start server
    try:
        with socketserver.TCPServer(("", PORT), TestServerHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:  # Address already in use
            print(f"\nError: Port {PORT} is already in use!")
            print("Either stop the other process or change the PORT variable in this script.")
        else:
            raise


if __name__ == "__main__":
    main()
