# YT Downloader Pro 🎬

A full-featured **YouTube Desktop Downloader** built with Python 3 + Tkinter, powered by **yt-dlp**. Supports high-quality video downloads, audio extraction, playlist management, a download queue with pause/resume, and can be packaged into a portable Windows `.exe`.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Dark UI** | Modern dark theme with YouTube-red accents |
| **Video Info** | Thumbnail preview, title, channel, duration, views |
| **Format Table** | All available qualities (360p → 8K) with codec, FPS, file size |
| **Audio Only** | Download audio and convert to MP3 (or M4A, AAC, WAV…) |
| **Playlist Support** | Detect playlists, pick individual videos or download all |
| **Download Queue** | Multi-item queue with animated progress bars |
| **Pause / Resume** | Pause and resume any download mid-way |
| **Auto-Retry** | Configurable retry attempts on failure |
| **Real-time Stats** | Download speed, percentage, and ETA shown live |
| **Download History** | Persistent JSON history with folder-open on double-click |
| **Settings** | Download folder, concurrency, audio quality, proxy, rate limit |
| **Drag & Drop** | Drop a YouTube URL directly onto the URL field |
| **Portable .exe** | Build a standalone Windows executable, no Python needed |

---

## 🗂 Project Structure

```
youtube downloader/
├── main.py                  ← Entry point
├── requirements.txt         ← pip dependencies
├── YTDownloader.spec        ← PyInstaller spec
├── build.bat                ← One-click build script
├── README.md
│
├── core/
│   ├── __init__.py
│   └── downloader.py        ← yt-dlp engine, threading, pause/resume
│
├── ui/
│   ├── __init__.py
│   ├── app.py               ← Main window
│   ├── download_panel.py    ← Queue panel + download cards
│   ├── settings_dialog.py   ← Settings modal
│   ├── history_dialog.py    ← Download history modal
│   ├── styles.py            ← TTK dark theme definitions
│   ├── theme.py             ← Colour palette & font constants
│   └── widgets.py           ← Reusable custom widgets
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py           ← URL validation, formatting helpers
│   └── settings.py          ← Persistent JSON settings manager
│
└── assets/
    └── icon.ico             ← (optional) window icon
```

---

## 🚀 Quick Start (Running from Source)

### 1. Prerequisites
- **Python 3.10+** – [download](https://www.python.org/downloads/)
- **pip** (bundled with Python)
- **ffmpeg** – required for audio conversion and video merging

### 2. Install ffmpeg
Download the latest Windows build from https://www.gyan.dev/ffmpeg/builds/ (choose `ffmpeg-release-essentials.zip`), extract, and add the `bin/` folder to your `PATH`.

### 3. Install Python dependencies
```bash
pip install yt-dlp Pillow requests
```
Or all at once:
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python main.py
```

---

## 📦 Building a Standalone .exe

The `.exe` bundles Python, all libraries, and the app into a single folder that anyone can run — no Python installation needed.

### Option A – Use the build script (easiest)
```bat
build.bat
```
The executable will be at `dist\YTDownloader\YTDownloader.exe`.

### Option B – Manual steps
```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller YTDownloader.spec --clean --noconfirm
```

### Option C – Bundle ffmpeg inside the .exe
1. Download `ffmpeg.exe` and `ffprobe.exe` from https://www.gyan.dev/ffmpeg/builds/
2. Place them in an `ffmpeg/` folder next to `YTDownloader.spec`
3. Un-comment the ffmpeg lines in `YTDownloader.spec`
4. Run the build

---

## ⚙️ Configuration

All settings are stored in `%APPDATA%\YTDownloader\settings.json` and `history.json`.

| Setting | Default | Description |
|---|---|---|
| `download_folder` | `~/Downloads` | Where files are saved |
| `concurrent_downloads` | `2` | Max parallel downloads |
| `audio_format` | `mp3` | Audio output format |
| `audio_quality` | `192` | Audio bitrate (kbps) |
| `open_folder_when_done` | `true` | Open Explorer on completion |
| `save_history` | `true` | Keep download history |
| `auto_retry` | `true` | Retry failed downloads |
| `retry_count` | `3` | Max retry attempts |
| `proxy` | `` | HTTP/SOCKS proxy URL |
| `rate_limit` | `` | Speed limit (e.g. `2M`, `500K`) |

---

## 📋 Dependencies

| Package | Purpose |
|---|---|
| `yt-dlp` | Video/audio downloading backend |
| `Pillow` | Thumbnail image display |
| `requests` | Thumbnail HTTP fetch |
| `pyinstaller` | Build standalone .exe (dev only) |

### Optional (for drag-and-drop)
```bash
pip install tkinterdnd2
```

---

## 🔒 Legal Notice

This tool is intended for **personal use only**. Always respect copyright laws and YouTube's Terms of Service. Only download content you have the right to download.

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `ffmpeg not found` | Install ffmpeg and add it to your PATH |
| Thumbnail not loading | Install Pillow: `pip install Pillow` |
| Download stuck at 0% | Check your internet connection |
| `.exe` crashes on launch | Run from console to see error: `YTDownloader.exe` in cmd |
| Age-restricted video | yt-dlp may need cookies; see yt-dlp docs |
