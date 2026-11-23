# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for YT Downloader Pro
============================================
Produces a one-folder distribution in /dist/YTDownloader/

Build command:
    pyinstaller YTDownloader.spec --clean

Optional: bundle ffmpeg binaries
  1. Download ffmpeg Windows build from https://www.gyan.dev/ffmpeg/builds/
  2. Copy ffmpeg.exe and ffprobe.exe into  ./ffmpeg/  next to this spec file
  3. Un-comment the FFMPEG section in Analysis.datas below
"""

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Extra hidden imports ─────────────────────────────────────────────────────
hidden = (
    collect_submodules('yt_dlp') +
    collect_submodules('PIL') +
    ['PIL._tkinter_finder', 'tkinter', 'tkinter.ttk', 'tkinter.filedialog',
     'tkinter.messagebox', 'requests', 'urllib3', 'charset_normalizer',
     'certifi', 'idna']
)

# ── Data files ───────────────────────────────────────────────────────────────
datas = collect_data_files('yt_dlp')

import os
for bin_name in ('ffmpeg.exe', 'ffprobe.exe'):
    bin_path = os.path.join('.', 'ffmpeg', bin_name)
    if os.path.isfile(bin_path):
        datas.append((bin_path, 'ffmpeg'))

icon_file = 'assets/icon.ico' if os.path.isfile('assets/icon.ico') else None
if icon_file:
    datas.append(('assets/icon.ico', 'assets'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt5', 'wx'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

version_file = 'version_info.txt' if os.path.isfile('version_info.txt') else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YTDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version=version_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YTDownloader',
)
