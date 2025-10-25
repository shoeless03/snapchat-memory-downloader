#!/bin/bash
# Build script for macOS and Linux

echo "============================================"
echo "Building Snapchat Memories Downloader"
echo "Platform: $(uname -s)"
echo "============================================"

# Install build dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements-build.txt

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf ../../build ../../dist

# Build with PyInstaller
echo ""
echo "Building executable..."
pyinstaller snapchat-memories.spec

# Determine platform name
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
else
    PLATFORM="linux"
fi

# Create distribution folder
echo ""
echo "Creating distribution package..."
mkdir -p "../../dist/snapchat-memories-downloader-${PLATFORM}"
cp "../../dist/snapchat-memories-downloader" "../../dist/snapchat-memories-downloader-${PLATFORM}/"
cp "../../docs/README-DISTRIBUTION.md" "../../dist/snapchat-memories-downloader-${PLATFORM}/README.md"
cp -r "../../docs/licenses" "../../dist/snapchat-memories-downloader-${PLATFORM}/"

# Make executable
chmod +x "../../dist/snapchat-memories-downloader-${PLATFORM}/snapchat-memories-downloader"

echo ""
echo "============================================"
echo "Build complete!"
echo "Output: ../../dist/snapchat-memories-downloader-${PLATFORM}/"
echo "============================================"
