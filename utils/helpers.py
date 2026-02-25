"""
Utility Helpers
===============
General-purpose helper functions shared across the application.
"""

import os
import re
import math
import hashlib
import datetime
from typing import Optional


# ──────────────────────────── URL Validation ────────────────────────────────

# Platforms supported natively by yt-dlp
_SUPPORTED_PATTERNS = [
    # YouTube
    r'(https?://)?(www\.)?youtube\.com/watch\?.*v=[\w-]+',
    r'(https?://)?youtu\.be/[\w-]+',
    r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
    r'(https?://)?(www\.)?youtube\.com/playlist\?.*list=[\w-]+',
    r'(https?://)?(www\.)?youtube\.com/@[\w-]+',
    r'(https?://)?(www\.)?youtube\.com/channel/[\w-]+',
    r'(https?://)?(www\.)?youtube\.com/c/[\w-]+',
    # Facebook
    r'(https?://)?(www\.)?facebook\.com/.*/(videos|reel|watch)/[\w/?=&]+',
    r'(https?://)?(www\.)?facebook\.com/watch(/live)?/?\?.*v=\d+',
    r'(https?://)?fb\.watch/[\w-]+',
    r'(https?://)?(www\.)?facebook\.com/reel/\d+',
    r'(https?://)?(m\.)?facebook\.com/[\w.]+/videos/\d+',
    # Instagram
    r'(https?://)?(www\.)?instagram\.com/(p|reel|tv)/[\w-]+',
    # Twitter / X
    r'(https?://)?(www\.)?(twitter|x)\.com/[\w]+/status/\d+',
    # TikTok
    r'(https?://)?(www\.)?tiktok\.com/@[\w.]+/video/\d+',
    r'(https?://)?vm\.tiktok\.com/[\w-]+',
    # Vimeo
    r'(https?://)?(www\.)?vimeo\.com/\d+',
    # Reddit
    r'(https?://)?(www\.)?reddit\.com/r/[\w]+/comments/[\w]+',
    # Twitch
    r'(https?://)?(www\.)?twitch\.tv/videos/\d+',
    r'(https?://)?(www\.)?twitch\.tv/[\w]+/clip/[\w-]+',
    # Generic fallback: any http/https URL with a video-like path
    r'https?://[^\s]+\.(mp4|webm|mkv|mov|avi)(\?.*)?$',
]


def is_valid_url(url: str) -> bool:
    """Return True if *url* looks like a URL supported by yt-dlp."""
    url = url.strip()
    return any(re.search(p, url, re.IGNORECASE) for p in _SUPPORTED_PATTERNS)


# Backwards-compat alias used elsewhere in the codebase
is_valid_youtube_url = is_valid_url


def is_playlist_url(url: str) -> bool:
    """Return True if the URL points to a YouTube playlist."""
    return 'list=' in url and 'youtube.com/playlist' in url


# ──────────────────────────── Size / Speed Formatting ───────────────────────

def format_bytes(num_bytes: Optional[float], suffix: str = "B") -> str:
    """Convert bytes to a human-readable string (KB / MB / GB …)."""
    if num_bytes is None:
        return "–"
    if num_bytes == 0:
        return "0 B"
    units = ("", "K", "M", "G", "T", "P")
    index = int(math.log(abs(num_bytes), 1024))
    index = min(index, len(units) - 1)
    value = num_bytes / (1024 ** index)
    return f"{value:.1f} {units[index]}{suffix}"


def format_speed(bytes_per_sec: Optional[float]) -> str:
    """Format download speed as a human-readable string."""
    if bytes_per_sec is None:
        return "–"
    return f"{format_bytes(bytes_per_sec)}/s"


def format_eta(seconds: Optional[float]) -> str:
    """Convert seconds into a HH:MM:SS or MM:SS ETA string."""
    if seconds is None or seconds < 0:
        return "–"
    seconds = int(seconds)
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h}:{m:02d}:{s:02d}"
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def format_duration(seconds: Optional[int]) -> str:
    """Format video duration in HH:MM:SS or MM:SS."""
    if seconds is None:
        return "–"
    return format_eta(seconds)


# ──────────────────────────── Filename Sanitisation ─────────────────────────

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1F]')


def sanitize_filename(name: str, max_length: int = 180) -> str:
    """Remove characters that are illegal in Windows filenames."""
    name = _INVALID_CHARS.sub('_', name)
    name = name.strip(". ")
    return name[:max_length] if len(name) > max_length else name


# ──────────────────────────── Path Helpers ──────────────────────────────────

def ensure_dir(path: str) -> str:
    """Create *path* (and parents) if it doesn't exist; return *path*."""
    os.makedirs(path, exist_ok=True)
    return path


def default_download_folder() -> str:
    """Return the user's Downloads folder (cross-platform)."""
    home = os.path.expanduser("~")
    dl = os.path.join(home, "Downloads")
    return dl if os.path.isdir(dl) else home


# ──────────────────────────── Hashing ───────────────────────────────────────

def short_id(text: str, length: int = 8) -> str:
    """Return a short hex digest that uniquely (enough) identifies *text*."""
    return hashlib.md5(text.encode()).hexdigest()[:length]


# ──────────────────────────── Timestamp ─────────────────────────────────────

def now_str() -> str:
    """ISO-8601 timestamp for the current local time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
