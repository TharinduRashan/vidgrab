# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — VidGrab  (SINGLE FILE build)
================================================
Produces:  dist\VidGrab.exe   ← one file, share this alone

Build:
    pyinstaller VidGrab.spec --clean

Optional — bundle ffmpeg so users don't need to install it:
  1. Download ffmpeg from https://www.gyan.dev/ffmpeg/builds/
     (get the "release essentials" zip)
  2. Copy  ffmpeg.exe  and  ffprobe.exe  into  ./ffmpeg/
  3. Un-comment the FFMPEG block below.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Hidden imports ───────────────────────────────────────────────────────────
hidden = (
    collect_submodules('yt_dlp') +
    collect_submodules('PIL') +
    [
        'PIL._tkinter_finder',
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
        'requests', 'urllib3', 'charset_normalizer', 'certifi', 'idna',
        'brotli',
    ]
)

# ── Data files ───────────────────────────────────────────────────────────────
datas = collect_data_files('yt_dlp')

# ── Bundle ffmpeg (extracted to ./ffmpeg/) ──────────────────────────────────
import os
datas += [
    ('./ffmpeg/ffmpeg.exe',   'ffmpeg'),
    ('./ffmpeg/ffprobe.exe',  'ffmpeg'),
]

# ── Optional: app icon ───────────────────────────────────────────────────────
# datas += [('./assets/icon.ico', 'assets')]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude heavy packages that are definitely not needed
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'PyQt5', 'PyQt6', 'wx', 'gi',
        'IPython', 'notebook', 'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── SINGLE FILE EXE ─────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # ← include binaries IN the exe
    a.zipfiles,      # ← include zipfiles IN the exe
    a.datas,         # ← include datas IN the exe
    name='VidGrab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,        # compress with UPX to reduce file size
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # no black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # un-comment if you have an .ico
)
