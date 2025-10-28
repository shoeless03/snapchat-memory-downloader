# Getting Started - Beginner's Guide

This guide will walk you through downloading and using the Snapchat Memories Downloader from start to finish. No technical experience required!

## Table of Contents

1. [Step 1: Request Your Snapchat Data](#step-1-request-your-snapchat-data)
2. [Step 2: Download the Pre-Built Executable](#step-2-download-the-pre-built-executable)
3. [Step 3: Set Up Your Folder Structure](#step-3-set-up-your-folder-structure)
4. [Step 4: Run the Tool](#step-4-run-the-tool)
5. [Step 5: Download Your Memories](#step-5-download-your-memories)
6. [Optional: Apply Overlays](#optional-apply-overlays)
7. [Troubleshooting](#troubleshooting)

---

## Step 1: Request Your Snapchat Data

Before you can use this tool, you need to get your data from Snapchat.

### How to Request Your Data from Snapchat:

1. **Open Snapchat** on your phone
2. **Go to Settings** (tap your profile icon, then the gear icon)
3. **Scroll down** to "Privacy Controls" or "My Data"
4. **Tap "My Data"** or "Download My Data"
5. **Select what to include:**
   - Make sure "Memories" is checked
   - You can uncheck other things to speed up the export
6. **Submit Request**
7. **Wait for email** - Snapchat will email you when your data is ready (usually 1-24 hours)
8. **Download the ZIP file** from the link in the email
9. **Extract the ZIP file** to a folder on your computer

After extraction, you should have a folder like `mydata_XXXXXXXXXX` containing:
- `index.html`
- `html/` folder
  - `memories_history.html` (this is the important file!)
  - Other HTML files

**Important:** Keep this folder safe - you'll need it in Step 3!

---

## Step 2: Download the Pre-Built Executable

No Python installation required! Just download the right version for your computer.

### For Windows Users:

1. **Go to the releases page:** [Latest Release](https://github.com/shoeless03/snapchat-memory-downloader/releases/latest)
2. **Download:** `snapchat-memories-downloader-windows.zip`
3. **Extract the ZIP file** by right-clicking and selecting "Extract All..."
4. **You'll get a folder** named `snapchat-memories-downloader-windows/` containing:
   - `snapchat-memories-downloader.exe` (this is the tool!)
   - `README.md` (documentation)
   - `licenses/` folder (legal stuff)

### For macOS Users:

1. **Go to the releases page:** [Latest Release](https://github.com/shoeless03/snapchat-memory-downloader/releases/latest)
2. **Download:** `snapchat-memories-downloader-macos.zip`
3. **Extract the ZIP file** by double-clicking it
4. **You'll get a folder** named `snapchat-memories-downloader-macos/` containing:
   - `snapchat-memories-downloader` (this is the tool!)
   - `README.md` (documentation)
   - `licenses/` folder (legal stuff)

**Mac Security Note:** First time running, you may need to:
- Right-click the file and select "Open"
- Click "Open" in the security dialog
- Or go to System Preferences > Security & Privacy and allow it

### For Linux Users:

1. **Go to the releases page:** [Latest Release](https://github.com/shoeless03/snapchat-memory-downloader/releases/latest)
2. **Download:** `snapchat-memories-downloader-linux.zip`
3. **Extract the ZIP file** in your file manager or with:
   ```bash
   unzip snapchat-memories-downloader-linux.zip
   ```
4. **Make it executable:**
   ```bash
   cd snapchat-memories-downloader-linux
   chmod +x snapchat-memories-downloader
   ```

---

## Step 3: Set Up Your Folder Structure

Now let's organize everything properly. This is **very important** for the tool to work!

### Recommended Setup:

Create a folder structure like this:

```
MySnapchatMemories/                          (create a new folder with any name)
├── snapchat-memories-downloader.exe         (the tool you downloaded)
└── data from snapchat/                      (rename your Snapchat export to exactly this)
    ├── index.html
    └── html/
        └── memories_history.html
```

### Step-by-Step Instructions:

1. **Create a new folder** anywhere on your computer
   - Name it something like `MySnapchatMemories` or `SnapchatDownload`
   - This is your "working folder"

2. **Move the executable** into this folder:
   - **Windows:** Move `snapchat-memories-downloader.exe`
   - **macOS/Linux:** Move `snapchat-memories-downloader`

3. **Move your Snapchat export folder** into this folder

4. **Rename the Snapchat folder** to exactly: `data from snapchat`
   - Original name was something like `mydata_XXXXXXXXXX`
   - **Must be renamed** to exactly `data from snapchat` (with spaces and lowercase)

Your folder should now look like:
```
MySnapchatMemories/
├── snapchat-memories-downloader.exe
└── data from snapchat/
    ├── index.html
    └── html/
        └── memories_history.html
```

**Why this matters:** The tool looks for a folder named exactly `data from snapchat` by default. You can use a different name, but you'll need to tell the tool where it is (see Step 4).

---

## Step 4: Run the Tool

Time to start downloading!

### Windows:

1. **Open File Explorer** and navigate to your working folder
2. **Double-click** `snapchat-memories-downloader.exe`
3. A **command prompt window** will open with the interactive menu

**Alternative method:**
1. **Right-click** in the folder while holding Shift
2. Select **"Open PowerShell window here"** or **"Open command window here"**
3. Type: `.\snapchat-memories-downloader.exe`
4. Press **Enter**

### macOS:

1. **Open Terminal** (Applications > Utilities > Terminal)
2. **Navigate to your folder:**
   ```bash
   cd /path/to/MySnapchatMemories
   ```
   (Tip: Type `cd ` then drag the folder into Terminal to auto-fill the path!)
3. **Run the tool:**
   ```bash
   ./snapchat-memories-downloader
   ```

### Linux:

1. **Open your terminal**
2. **Navigate to your folder:**
   ```bash
   cd /path/to/MySnapchatMemories
   ```
3. **Run the tool:**
   ```bash
   ./snapchat-memories-downloader
   ```

---

## Step 5: Download Your Memories

When you run the tool, you'll see an **interactive menu** with ASCII art and several options.

### Using the Interactive Menu:

```
   ____                        _           _
  / ___| _ __   __ _ _ __   __| |__   __ _| |_
  \___ \| '_ \ / _` | '_ \ / _` |_ \ / _` | __|
   ___) | | | | (_| | |_) | (_| |) | (_| | |_
  |____/|_| |_|\__,_| .__/ \__,_|_/\__,_|\__|
                    |_|
  __  __                           _
 |  \/  | ___ _ __ ___   ___  _ __(_) ___  ___
 | |\/| |/ _ \ '_ ` _ \ / _ \| '__| |/ _ \/ __|
 | |  | |  __/ | | | | | (_) | |  | |  __/\__ \
 |_|  |_|\___|_| |_| |_|\___/|_|  |_|\___||___/

[>>] Download memories
[+]  Apply overlays to images and videos
[?]  Verify downloads
[*]  Verify composited files
[~]  Convert timezone (UTC to local)
[X]  Exit

What would you like to do?
```

**Navigation:**
- Use **↑** and **↓** arrow keys to move between options
- Press **Enter** to select an option

### To Download Your Memories:

1. **Use arrow keys** to highlight `[>>] Download memories`
2. **Press Enter**
3. The tool will:
   - Check for required files
   - Start downloading your memories
   - Show progress for each file
   - Save files to `memories/` folder

**What you'll see:**
```
[20:49:29] Downloading 430 memories...
[20:49:29] [1/430 0.2%] OK 2025-10-16_194703_Image_9ce001ca.jpg | ETA: 850s
[20:49:31] [2/430 0.5%] OK 2025-09-24_161956_Image_5b617512.jpg | ETA: 848s
...
```

**Where files are saved:**
- `memories/images/` - Your photos
- `memories/videos/` - Your videos
- `memories/overlays/` - Snapchat stickers/text/filters

**File naming format:**
```
2025-10-16_194703_Image_9ce001ca.jpg
└─────┬─────┘ └──┬──┘ └──┬───┘ └┬┘ └┬┘
      │          │       │      │   └─ Extension
      │          │       │      └───── Short ID (from Snapchat)
      │          │       └──────────── Media type (Image or Video)
      │          └──────────────────── Time (HH:MM:SS)
      └─────────────────────────────── Date (YYYY-MM-DD)
```

### If Download is Interrupted:

**Don't worry!** Just run the tool again and select "Download memories". It will:
- Skip files you already downloaded
- Continue where it left off
- Show you progress

---

## Optional: Apply Overlays

Snapchat provides overlays (stickers, text, filters) as separate PNG files. You can combine them back onto your photos and videos to recreate the original Snapchat look!

### Requirements:

**Already included in the executable:**
- Pillow (for images)

**Optional installs for extra features:**
- **FFmpeg** (for videos) - [Download here](https://ffmpeg.org/download.html)
- **ExifTool** (to preserve GPS data) - [Download here](https://exiftool.org/)

### How to Apply Overlays:

1. **Run the tool** again
2. **Select:** `[+] Apply overlays to images and videos`
3. **Choose options:**
   - "Both images and videos" (if you have FFmpeg)
   - "Only images" (if you don't have FFmpeg)
4. Press **Enter** to start

**What happens:**
- Original files remain untouched in `memories/images/` and `memories/videos/`
- New composited files are created in `memories/composited/images/` and `memories/composited/videos/`
- Progress shown with ETA

**Performance:**
- **Without ExifTool:** ~10 images/second
- **With ExifTool:** ~0.6 images/second (slower, but preserves GPS coordinates)

**Example output:**
```
[20:49:29] Compositing 430 images...
[20:49:29] Metadata copying enabled (ExifTool detected)
[20:49:29] [1/430 0.2%] OK 2025-10-16_194703_Image_9ce001ca.jpg | 0.6 img/s | ETA: 715s
[20:49:30] [2/430 0.5%] OK 2025-09-24_161956_Image_5b617512.jpg | 0.6 img/s | ETA: 713s
...
[20:59:44] Completed in 615.3s (1.43s per image)
[20:59:44] Images: 430 composited, 0 failed, 0 skipped
```

---

## Troubleshooting

### Problem: "File not found" or "memories_history.html not found"

**Solution:**
- Make sure your Snapchat export folder is named exactly `data from snapchat`
- Check that `memories_history.html` exists in `data from snapchat/html/`
- Or specify custom path in the menu when prompted

### Problem: Downloads are very slow or failing

**Solution:**
- Snapchat rate-limits downloads
- The tool automatically retries with delays
- If it keeps failing, try again later (Snapchat may be throttling you)
- Check your internet connection

### Problem: "File is not a zip file" errors

**Solution:**
- This happens when Snapchat rate-limits you
- The tool will automatically retry
- Just run the tool again - it will pick up where it left off
- Consider taking breaks between downloads if this happens a lot

### Problem: (Windows) "Windows protected your PC" warning

**Solution:**
- Click **"More info"**
- Click **"Run anyway"**
- This happens because the executable isn't code-signed (costs money!)
- The code is open source and safe to run

### Problem: (Mac) "Cannot open because developer cannot be verified"

**Solution:**
1. **Right-click** the executable
2. Select **"Open"**
3. Click **"Open"** in the dialog
4. Or go to **System Preferences > Security & Privacy** and click "Open Anyway"

### Problem: Missing GPS coordinates in photos

**Solution:**
- Install ExifTool (see [Optional Dependencies](../README.md#optional-dependencies))
- Run `Apply overlays` again - it will update the files with GPS data

### Problem: Can't composite videos

**Solution:**
- Install FFmpeg (see [Optional Dependencies](../README.md#optional-dependencies))
- Windows: Add FFmpeg to your PATH environment variable
- macOS/Linux: Install via package manager

### Problem: Files have wrong dates

**Solution:**
- By default, files use UTC timezone (Snapchat's format)
- Use the **"Convert timezone"** option in the menu to convert to your local timezone
- This will update both filenames and file timestamps

---

## What's Next?

After downloading:
- Your memories are in `memories/images/` and `memories/videos/`
- Files are named with timestamps for easy sorting
- File dates match when you took them in Snapchat
- You can safely back up, move, or edit these files

**Verify your downloads:**
- Select `[?] Verify downloads` from the menu
- Shows you what's downloaded and what's missing

**Apply overlays:**
- Select `[+] Apply overlays` to recreate the Snapchat look
- Creates new files in `memories/composited/` folder

**Convert to local time:**
- Select `[~] Convert timezone` to change from UTC to your local timezone
- Updates both filenames and file timestamps

---

## Need More Help?

- **Full documentation:** [README.md](../README.md)
- **Report issues:** [GitHub Issues](https://github.com/shoeless03/snapchat-memory-downloader/issues)
- **Support development:** [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X21N8LO2)

---

**Happy downloading!** Enjoy your organized Snapchat memories.
