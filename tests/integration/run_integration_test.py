#!/usr/bin/env python3
"""
Quick integration test runner.
Runs a complete end-to-end test of the downloader.
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a command and return True if successful."""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, text=True)
        print(f"\n✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} - FAILED")
        print(f"Error: {e}")
        return False
    except FileNotFoundError as e:
        print(f"\n✗ {description} - FAILED")
        print(f"Error: {e}")
        print("Make sure Python is in your PATH")
        return False


def cleanup(test_dir):
    """Clean up test output directories."""
    import shutil

    memories_dir = test_dir / "memories"
    if memories_dir.exists():
        print(f"\n  Removing {memories_dir}")
        shutil.rmtree(memories_dir)

    progress_file = test_dir / "download_progress.json"
    if progress_file.exists():
        print(f"  Removing {progress_file}")
        progress_file.unlink()

    cache_file = test_dir / "overlay_pairs.json"
    if cache_file.exists():
        print(f"  Removing {cache_file}")
        cache_file.unlink()


def main():
    """Run integration tests."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    print("="*60)
    print("Snapchat Memories Downloader - Integration Test")
    print("="*60)
    print(f"Test directory: {script_dir}")
    print(f"Project root: {project_root}")

    # Step 0: Clean up any previous test runs
    print(f"\n{'='*60}")
    print("▶ Cleanup: Removing previous test runs")
    print(f"{'='*60}")
    cleanup(script_dir)
    print("✓ Cleanup complete")

    # Step 1: Generate test files
    if not run_command(
        [sys.executable, "create_test_files.py"],
        "Step 1/5: Generate test files",
        cwd=script_dir
    ):
        return False

    # Step 2: Start test server in background
    print(f"\n{'='*60}")
    print("▶ Step 2/5: Start test server")
    print(f"{'='*60}")

    server_process = subprocess.Popen(
        [sys.executable, "test_server.py"],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("Waiting for server to start...")
    time.sleep(3)

    if server_process.poll() is not None:
        print("✗ Server failed to start")
        stdout, stderr = server_process.communicate()
        print(f"Output: {stdout}")
        print(f"Error: {stderr}")
        return False

    print("✓ Server started (PID: {})".format(server_process.pid))

    try:
        # Step 3: Run downloader
        if not run_command(
            [
                sys.executable,
                "download_snapchat_memories.py",
                "--html", "tests/integration/data from snapchat/html/memories_history.html",
                "--output", "tests/integration/memories",
                "--delay", "0.5"
            ],
            "Step 3/5: Download memories",
            cwd=project_root
        ):
            return False

        # Step 4: Verify downloads
        if not run_command(
            [
                sys.executable,
                "download_snapchat_memories.py",
                "--html", "tests/integration/data from snapchat/html/memories_history.html",
                "--output", "tests/integration/memories",
                "--verify"
            ],
            "Step 4/5: Verify downloads",
            cwd=project_root
        ):
            return False

        # Step 5: Test overlay compositing
        if not run_command(
            [
                sys.executable,
                "download_snapchat_memories.py",
                "--html", "tests/integration/data from snapchat/html/memories_history.html",
                "--output", "tests/integration/memories",
                "--apply-overlays"
            ],
            "Step 5/5: Composite overlays",
            cwd=project_root
        ):
            return False

        # Success!
        print(f"\n{'='*60}")
        print("✓✓✓ ALL INTEGRATION TESTS PASSED! ✓✓✓")
        print(f"{'='*60}")

        memories_dir = script_dir / "memories"
        print(f"\nTest output available in: {memories_dir}")
        print("\nGenerated files:")
        for subdir in ["images", "videos", "overlays", "composited/images", "composited/videos"]:
            path = memories_dir / subdir
            if path.exists():
                count = len(list(path.glob("*")))
                print(f"  • {subdir:20s}: {count} files")

        return True

    finally:
        # Stop server
        print(f"\n{'='*60}")
        print("▶ Stopping test server")
        print(f"{'='*60}")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✓ Server stopped")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("✓ Server killed")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
