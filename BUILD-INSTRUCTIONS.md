# Build Instructions

Guide for building platform-specific executables of Snapchat Memories Downloader.

## Overview

**Yes, you need separate builds for each platform:**
- **Windows:** `.exe` file (built on Windows)
- **macOS:** Unix executable (built on macOS)
- **Linux:** Unix executable (built on Linux)

PyInstaller creates platform-specific binaries that include Python and all dependencies.

## Prerequisites

### All Platforms
- Python 3.11 or higher
- pip package manager
- Git (to clone/manage the repository)

### Platform-Specific

**Windows:**
- Visual Studio Build Tools (for pywin32)
- Or: Full Visual Studio installation

**macOS:**
- Xcode Command Line Tools: `xcode-select --install`

**Linux:**
- Build essentials: `sudo apt-get install build-essential python3-dev`

## Quick Build

### Windows

```cmd
git clone https://github.com/shoeless03/snapchat-memory-downloader.git
cd snapchat-memory-downloader
git checkout packaging
build-windows.bat
```

Output: `dist\snapchat-memories-downloader-windows\`

### macOS / Linux

```bash
git clone https://github.com/shoeless03/snapchat-memory-downloader.git
cd snapchat-memory-downloader
git checkout packaging
chmod +x build-unix.sh
./build-unix.sh
```

Output: `dist/snapchat-memories-downloader-macos/` or `dist/snapchat-memories-downloader-linux/`

## Manual Build Process

If the scripts don't work, build manually:

### 1. Install Dependencies

```bash
pip install -r requirements-build.txt
```

### 2. Build with PyInstaller

```bash
pyinstaller snapchat-memories.spec
```

### 3. Package Distribution

**Windows:**
```cmd
mkdir dist\snapchat-memories-downloader-windows
copy dist\snapchat-memories-downloader.exe dist\snapchat-memories-downloader-windows\
copy README-DISTRIBUTION.md dist\snapchat-memories-downloader-windows\README.md
xcopy /s licenses dist\snapchat-memories-downloader-windows\licenses\
```

**macOS/Linux:**
```bash
mkdir -p dist/snapchat-memories-downloader-{platform}
cp dist/snapchat-memories-downloader dist/snapchat-memories-downloader-{platform}/
cp README-DISTRIBUTION.md dist/snapchat-memories-downloader-{platform}/README.md
cp -r licenses dist/snapchat-memories-downloader-{platform}/
chmod +x dist/snapchat-memories-downloader-{platform}/snapchat-memories-downloader
```

Replace `{platform}` with `macos` or `linux`.

## Build Output

Each platform build creates a folder with:
```
snapchat-memories-downloader-{platform}/
├── snapchat-memories-downloader[.exe]  # Executable
├── README.md                           # User documentation
└── licenses/                           # Third-party licenses
    ├── LICENSE-requests.txt
    ├── LICENSE-Pillow.txt
    ├── LICENSE-pywin32.txt
    └── THIRD-PARTY-NOTICES.txt
```

## Distribution

### Creating Releases

1. **Build on each platform:**
   - Windows machine → Windows build
   - macOS machine → macOS build
   - Linux machine → Linux build

2. **Create ZIP archives:**
   ```bash
   # Windows (PowerShell)
   Compress-Archive -Path dist\snapchat-memories-downloader-windows -DestinationPath snapchat-memories-downloader-windows.zip

   # macOS/Linux
   zip -r snapchat-memories-downloader-macos.zip dist/snapchat-memories-downloader-macos
   zip -r snapchat-memories-downloader-linux.zip dist/snapchat-memories-downloader-linux
   ```

3. **Upload to GitHub Releases:**
   - Tag version: `git tag v1.0.0 && git push origin v1.0.0`
   - Create release on GitHub
   - Upload all three ZIP files

### File Sizes

Typical executable sizes:
- **Windows:** ~15-25 MB (includes pywin32)
- **macOS:** ~15-20 MB
- **Linux:** ~15-20 MB

## Testing Builds

Before distributing, test the executable:

1. **Copy to clean test directory** (no Python installed)
2. **Run executable:**
   ```bash
   ./snapchat-memories-downloader --help
   ```
3. **Test basic functionality:**
   ```bash
   ./snapchat-memories-downloader --verify
   ```
4. **Test with small HTML file** to verify downloads work

## Troubleshooting

### Build Fails: "No module named 'win32api'"

**Windows only** - Install Visual Studio Build Tools or full Visual Studio.

### Build Fails: "Permission denied"

**macOS/Linux** - Make build script executable:
```bash
chmod +x build-unix.sh
```

### Executable is Huge (>50MB)

This can happen if PyInstaller includes unnecessary packages. Check what's included:
```bash
pyinstaller --analyze snapchat-memories.spec
```

### "Not a valid Win32 application" Error

Built on wrong platform. Windows .exe must be built on Windows.

### macOS: "Cannot be opened because the developer cannot be verified"

Users need to:
1. Right-click executable
2. Select "Open"
3. Click "Open" in security dialog

Or run: `xattr -cr snapchat-memories-downloader`

### Linux: "Permission denied"

Executable not marked as executable:
```bash
chmod +x snapchat-memories-downloader
```

## Cross-Platform Considerations

### You CANNOT:
- Build Windows .exe on macOS/Linux
- Build macOS executable on Windows/Linux
- Build Linux executable on Windows/macOS

### You CAN:
- Use virtual machines to build for other platforms
- Use GitHub Actions to build all platforms automatically
- Use cloud build services

### Recommended: GitHub Actions

Create `.github/workflows/build.yml` to automatically build all platforms on every release tag.

## Size Optimization

To reduce executable size:

1. **Exclude unused modules in `.spec` file:**
   ```python
   excludes=['tkinter', 'matplotlib', 'scipy', 'numpy']
   ```

2. **Use UPX compression** (enabled by default):
   ```python
   upx=True
   ```

3. **Single file vs folder:**
   - Single file (current): Slower startup, easier distribution
   - Folder mode: Faster startup, multiple files

## Legal Compliance

Each build includes:
- `licenses/` folder with all third-party licenses
- `THIRD-PARTY-NOTICES.txt` with attribution
- `README.md` with usage instructions

**Before distributing, verify:**
- All license files are present
- Third-party notices are accurate
- README correctly attributes dependencies

## Automated Builds (Future)

For automated multi-platform builds, consider:

1. **GitHub Actions** - Free for public repos
2. **Travis CI** - Multi-platform support
3. **AppVeyor** - Windows builds
4. **CircleCI** - macOS/Linux builds

Example GitHub Actions workflow available in separate documentation.

---

## Quick Reference

| Platform | Build On | Output Name | File Extension |
|----------|----------|-------------|----------------|
| Windows  | Windows  | snapchat-memories-downloader | `.exe` |
| macOS    | macOS    | snapchat-memories-downloader | (none) |
| Linux    | Linux    | snapchat-memories-downloader | (none) |

**Build Command:**
- Windows: `build-windows.bat`
- macOS/Linux: `./build-unix.sh`

**Test Command:**
```bash
./snapchat-memories-downloader --help
```
