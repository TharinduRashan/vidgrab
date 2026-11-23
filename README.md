# VidGrab 🎬

<p align="center">
  <img src="assets/icon.ico" alt="VidGrab Logo" width="96" height="96" />
</p>

<p align="center">
  <strong>Fast, Modern & Reliable Desktop Video and Audio Downloader</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" alt="Platform: Windows" />
  <img src="https://img.shields.io/badge/Powered%20By-yt--dlp-red" alt="Powered by yt-dlp" />
  <img src="https://img.shields.io/badge/GUI-Tkinter%20%2F%20TTK-4B8BBE" alt="Tkinter GUI" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT" />
  <img src="https://img.shields.io/badge/Tests-Passing-success" alt="Tests: Passing" />
</p>

---

## 📖 Overview

**VidGrab** is a high-performance, desktop media downloader powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and built with Python 3 and Tkinter. It delivers a native desktop experience with custom dark and light themes, an interactive format table with real-time column sorting, audio extraction, playlist batch downloading, multi-task download queue with pause/resume, and portable single-file Windows executable packaging.

---

## ✨ Key Features

| Feature | Details |
|---|---|
| 🌓 **Dual Themes** | Sleek Dark Mode (default) and Light Mode with instantaneous in-place re-theming. |
| 🌐 **Multi-Platform** | Native support for YouTube (Shorts, Live streams, Embeds), Facebook, Instagram, TikTok, Twitter/X, Vimeo, SoundCloud, Reddit, Twitch, Dailymotion, and generic video links. |
| 📊 **Interactive Format Table** | Live stream inspector showing Resolution, FPS, Codec, File Size, Stream Type, and Format ID. Click column headers to sort ascending or descending. |
| 🎵 **Audio Extraction** | Convert audio directly to MP3, M4A, WAV, Opus, or AAC with selectable bitrates (128 kbps – 320 kbps). |
| 📋 **Playlist Manager** | Auto-detect playlists, preview full track lists, download selected items or batch-queue the entire playlist in one click. |
| ⚡ **Parallel Queue Manager** | Concurrent download limiter, live download speed, ETA countdown, and animated progress bars. |
| ⏸️ **Pause / Resume / Cancel** | Full thread-safe control over active downloads with automatic partial file (`.part`, `.ytdl`) cleanup on cancel. |
| 🔁 **Auto-Retry** | Configurable exponential backoff retry system for handling transient network dropouts. |
| 📜 **Persistent History** | Local JSON history log with double-click to reveal and highlight files directly in Windows Explorer. |
| ⚙️ **Customizable Settings** | Configure download directory, parallel concurrency slots, proxy servers, audio bitrate, and bandwidth limits. |
| 🚀 **Single-File `.exe`** | One-click build script (`build.bat`) producing a portable `dist\VidGrab.exe` with embedded icon and Windows Taskbar integration. |

---

## 🌐 Supported Platforms

VidGrab supports hundreds of video and audio sites powered by yt-dlp, including:

- **YouTube**: Standard videos, Shorts, Live streams (`youtube.com/live/`), Playlists, and Embedded links
- **Facebook**: Public videos, Reels, and Watch clips
- **Instagram**: Reels, Posts, and Videos
- **TikTok**: Videos and short clips
- **Twitter / X**: Video tweets and statuses
- **Vimeo**: HD and 4K videos
- **SoundCloud**: Tracks and audio streams
- **Reddit**: Embedded player videos
- **Twitch**: Clips and past broadcasts
- **Dailymotion**: HD video channels
- **Direct Video Streams**: Any direct `.mp4`, `.webm`, `.mkv`, `.mov`, `.avi`, or `.mp3` URL

---

## 🗂 Project Structure

```
vidgrab/
├── main.py                  ← Main application entry point (Windows AppUserModelID setup)
├── requirements.txt         ← Python package dependencies
├── VidGrab.spec             ← PyInstaller spec for single-file standalone .exe
├── YTDownloader.spec        ← Alternative PyInstaller spec for directory distribution
├── build.bat                ← One-click Windows build script
├── version_info.txt         ← Windows PE metadata (Explorer & Task Manager details)
├── README.md                ← Project documentation
│
├── core/
│   ├── __init__.py
│   └── downloader.py        ← Multi-threaded yt-dlp engine, queueing, pause/resume
│
├── ui/
│   ├── __init__.py
│   ├── app.py               ← Main application controller & tabbed interface
│   ├── download_panel.py    ← Queue cards, progress bars & action buttons
│   ├── settings_dialog.py   ← Settings modal dialog
│   ├── history_dialog.py    ← Download history viewer with Explorer reveal
│   ├── styles.py            ← TTK custom dark/light theme definitions
│   ├── theme.py             ← Palette manager, fonts & dynamic re-theming
│   └── widgets.py           ← Reusable UI components (progress bar, badges, tooltips)
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py           ← URL validation, size/speed/ETA formatters, sanitization
│   └── settings.py          ← Persistent JSON settings & history store
│
├── assets/
│   └── icon.ico             ← Multi-resolution application & executable icon
│
└── tests/
    └── test_vidgrab.py      ← Automated unit and regression test suite
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.10 through 3.14)
- **ffmpeg** (required for stream merging and audio format conversion)

#### Installing ffmpeg on Windows:
1. Download the latest release from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (choose `ffmpeg-release-essentials.zip`).
2. Extract the archive and copy `ffmpeg.exe` and `ffprobe.exe` into:
   - Your system `PATH`, **OR**
   - Directly inside an `ffmpeg/` folder inside the `vidgrab` directory (VidGrab will detect it automatically!).

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/vidgrab.git
cd vidgrab
pip install -r requirements.txt
```

### 3. Run the App

```bash
python main.py
```

---

## 📦 Building a Standalone Windows Executable

You can compile VidGrab into a single portable `.exe` file (`dist\VidGrab.exe`) that runs on any 64-bit Windows machine without needing Python.

### Option A: One-Click Build Script (Recommended)
Simply double-click or run:
```bat
build.bat
```
The script will install build dependencies, compile the single executable, embed the icon and version metadata, and output `dist\VidGrab.exe`.

### Option B: Manual PyInstaller Build
```bash
pip install -r requirements.txt
pyinstaller VidGrab.spec --clean --noconfirm
```

### Optional: Bundle ffmpeg inside the `.exe`
To make the `.exe` completely self-contained (users won't even need ffmpeg installed):
1. Place `ffmpeg.exe` and `ffprobe.exe` into an `ffmpeg/` folder inside the project root.
2. Run `build.bat`.
3. `VidGrab.spec` will automatically detect the binaries and bundle them into `VidGrab.exe`.

---

## ⚙️ Configuration & Data Storage

Settings and download logs are automatically persisted in `%APPDATA%\YTDownloader\`:
- `settings.json`: User configurations
- `history.json`: Download log

| Setting | Default | Description |
|---|---|---|
| `download_folder` | `~/Downloads` | Default folder where files are saved |
| `concurrent_downloads` | `2` | Number of simultaneous active downloads |
| `audio_format` | `mp3` | Target format for audio downloads (`mp3`, `m4a`, `wav`, `opus`, `aac`) |
| `audio_quality` | `192` | Audio bitrate in kbps (`128`, `160`, `192`, `256`, `320`) |
| `open_folder_when_done` | `true` | Automatically open folder in Windows Explorer on completion |
| `save_history` | `true` | Record completed downloads to history log |
| `auto_retry` | `true` | Automatically retry downloads on network failure |
| `retry_count` | `3` | Maximum retry attempts per item |
| `proxy` | `""` | Optional HTTP / SOCKS proxy (e.g. `socks5://127.0.0.1:9050`) |
| `rate_limit` | `""` | Bandwidth throttling (e.g. `2M` for 2 MB/s, `500K` for 500 KB/s) |

---

## 🧪 Testing

The codebase includes an automated test suite verifying URL validation, format sorting, size/speed/ETA formatters, settings persistence, UI widgets, and thread lifecycle.

To run tests:

```bash
python -m pytest -v
```

---

## 🛠️ Troubleshooting

| Issue | Resolution |
|---|---|
| **Audio conversion fails / Merge error** | Ensure `ffmpeg` is installed on PATH or placed in `./ffmpeg/`. |
| **YouTube blocks or throttles** | Update yt-dlp to latest version: `pip install --upgrade yt-dlp`. |
| **Taskbar shows Python logo instead of VidGrab** | Run via compiled `dist\VidGrab.exe` or ensure `SetCurrentProcessExplicitAppUserModelID` is active (handled automatically in `main.py`). |
| **Age-restricted or private videos** | Pass cookies or credentials using yt-dlp browser cookie flags. |

---

## ⚖️ Legal & Disclaimer

VidGrab is an open-source tool intended for personal backups and downloading content that you have explicit permission or rights to access. Please respect the Terms of Service of all content platforms and copyright laws in your jurisdiction.

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
