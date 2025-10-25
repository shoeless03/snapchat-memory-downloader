@echo off
REM Build script for Windows

echo ============================================
echo Building Snapchat Memories Downloader
echo Platform: Windows
echo ============================================

REM Install build dependencies
echo.
echo Installing dependencies...
pip install -r requirements-build.txt

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with PyInstaller
echo.
echo Building executable...
pyinstaller snapchat-memories.spec

REM Create distribution folder
echo.
echo Creating distribution package...
if not exist "dist\snapchat-memories-downloader-windows" mkdir "dist\snapchat-memories-downloader-windows"
copy "dist\snapchat-memories-downloader.exe" "dist\snapchat-memories-downloader-windows\"
copy "README-DISTRIBUTION.md" "dist\snapchat-memories-downloader-windows\README.md"
xcopy /s /i "licenses" "dist\snapchat-memories-downloader-windows\licenses"

echo.
echo ============================================
echo Build complete!
echo Output: dist\snapchat-memories-downloader-windows\
echo ============================================
pause
