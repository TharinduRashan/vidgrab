"""
YouTube Desktop Downloader - Main Entry Point
=============================================
Author: YouTube Downloader App
License: MIT
"""

import sys
import os

# Ensure bundled ffmpeg is on PATH (for PyInstaller builds)
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    ffmpeg_path = os.path.join(base_dir, 'ffmpeg')
    if os.path.isdir(ffmpeg_path):
        os.environ['PATH'] = ffmpeg_path + os.pathsep + os.environ.get('PATH', '')

from ui.app import YoutubeDownloaderApp

if __name__ == '__main__':
    app = YoutubeDownloaderApp()
    app.run()
