"""
Download Manager Core
=====================
Wraps yt-dlp to provide:
  - Video info fetching (formats, thumbnail URL, playlist detection)
  - Multi-threaded downloading with progress callbacks
  - Pause / Resume / Cancel via threading events
  - Automatic retry on failure
  - Audio-only → MP3 conversion via ffmpeg post-processor
"""

import os
import re
import threading
import time
from enum import Enum, auto
from typing import Callable, Dict, List, Optional

import yt_dlp

from utils.helpers import sanitize_filename, format_bytes, now_str
from utils.settings import settings


# ─────────────────────── Status Enum ────────────────────────────────────────

class DownloadStatus(Enum):
    QUEUED    = auto()
    FETCHING  = auto()
    ACTIVE    = auto()
    PAUSED    = auto()
    COMPLETED = auto()
    FAILED    = auto()
    CANCELLED = auto()


# ─────────────────────── Download Item ──────────────────────────────────────

class DownloadItem:
    """
    Represents a single download task.

    Attributes
    ----------
    url        : source URL
    title      : video title (populated after fetch)
    format_id  : yt-dlp format id to download
    audio_only : if True, extract audio → MP3
    output_dir : destination folder
    status     : current DownloadStatus
    progress   : 0–100 float
    speed      : bytes/s (float)
    eta        : seconds remaining (float)
    error      : last error message
    filepath   : absolute path of downloaded file
    """

    def __init__(
        self,
        url: str,
        title: str = "",
        format_id: str = "bestvideo+bestaudio/best",
        audio_only: bool = False,
        output_dir: str = "",
        thumbnail_url: str = "",
    ):
        self.url          = url
        self.title        = title or url
        self.format_id    = format_id
        self.audio_only   = audio_only
        self.output_dir   = output_dir or settings.get("download_folder")
        self.thumbnail_url = thumbnail_url

        self.status   : DownloadStatus = DownloadStatus.QUEUED
        self.progress : float          = 0.0
        self.speed    : float          = 0.0
        self.eta      : float          = 0.0
        self.error    : str            = ""
        self.filepath : str            = ""

        # threading controls
        self._pause_event  = threading.Event()
        self._cancel_event = threading.Event()
        self._pause_event.set()   # not paused initially

    # ── Controls ───────────────────────────────────────────────────────────

    def pause(self):
        self._pause_event.clear()
        self.status = DownloadStatus.PAUSED

    def resume(self):
        self._pause_event.set()
        if self.status == DownloadStatus.PAUSED:
            self.status = DownloadStatus.ACTIVE

    def cancel(self):
        self._cancel_event.set()
        self._pause_event.set()  # unblock if paused
        self.status = DownloadStatus.CANCELLED

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def wait_if_paused(self):
        """Block the download thread while paused."""
        self._pause_event.wait()


# ─────────────────────── yt-dlp Progress Hook ───────────────────────────────

class _ProgressHook:
    """Translates yt-dlp progress dicts into DownloadItem attribute updates."""

    def __init__(self, item: DownloadItem, on_progress: Callable):
        self._item        = item
        self._on_progress = on_progress

    def __call__(self, d: dict):
        item = self._item

        # Allow pause between chunks
        item.wait_if_paused()
        if item.is_cancelled():
            raise yt_dlp.utils.DownloadCancelled()

        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes") or 0
            total      = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            item.progress = (downloaded / total * 100) if total else 0
            item.speed    = d.get("speed") or 0.0
            item.eta      = d.get("eta") or 0.0
            item.status   = DownloadStatus.ACTIVE
        elif status == "finished":
            item.progress = 100.0
            item.filepath = d.get("filename", "")
        elif status == "error":
            item.error  = str(d.get("error", "Unknown error"))

        if self._on_progress:
            self._on_progress(item)


# ─────────────────────── Core Downloader ────────────────────────────────────

class Downloader:
    """
    Main download engine.

    Usage
    -----
    dl = Downloader()
    info = dl.fetch_info("https://youtu.be/xxxx")
    item = dl.create_item(url, format_id="137+140", title=info["title"])
    dl.enqueue(item, on_progress=my_callback, on_done=my_done_callback)
    """

    def __init__(self):
        self._semaphore = threading.Semaphore(settings.get("concurrent_downloads", 2))
        self._lock      = threading.Lock()

    # ── Info Fetching ──────────────────────────────────────────────────────

    def fetch_info(self, url: str) -> dict:
        """
        Fetch video / playlist metadata without downloading.

        Returns a dict matching yt-dlp's info_dict format.
        Raises yt_dlp.utils.DownloadError on failure.
        """
        ydl_opts = {
            "quiet":           True,
            "no_warnings":     True,
            "skip_download":   True,
            "extract_flat":    "in_playlist",
            "force_generic_extractor": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info

    def fetch_formats(self, url: str) -> dict:
        """
        Fetch full format list for a single video (not playlist).

        Returns the complete info_dict including 'formats'.
        """
        ydl_opts = {
            "quiet":         True,
            "no_warnings":   True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info

    # ── Download ───────────────────────────────────────────────────────────

    def enqueue(
        self,
        item: DownloadItem,
        on_progress: Optional[Callable] = None,
        on_done: Optional[Callable]     = None,
    ) -> threading.Thread:
        """
        Spawn a daemon thread that will download *item* when a semaphore slot
        is free.  Returns the thread immediately.
        """
        t = threading.Thread(
            target=self._download_worker,
            args=(item, on_progress, on_done),
            daemon=True,
            name=f"dl-{id(item)}",
        )
        t.start()
        return t

    def _download_worker(
        self,
        item: DownloadItem,
        on_progress: Optional[Callable],
        on_done: Optional[Callable],
    ):
        """Worker that respects the semaphore (concurrent download limit)."""
        with self._semaphore:
            if item.is_cancelled():
                return
            item.status = DownloadStatus.ACTIVE
            self._run_download(item, on_progress)

        # Retry logic
        max_retries = settings.get("retry_count", 3) if settings.get("auto_retry") else 0
        attempt = 0
        while item.status == DownloadStatus.FAILED and attempt < max_retries:
            attempt += 1
            item.error  = f"Retrying… attempt {attempt}/{max_retries}"
            item.status = DownloadStatus.QUEUED
            if on_progress:
                on_progress(item)
            time.sleep(2 * attempt)   # back-off
            with self._semaphore:
                if item.is_cancelled():
                    break
                item.status = DownloadStatus.ACTIVE
                self._run_download(item, on_progress)

        if on_done:
            on_done(item)

        # Save to history
        if item.status == DownloadStatus.COMPLETED:
            settings.append_history({
                "title":    item.title,
                "url":      item.url,
                "path":     item.filepath,
                "date":     now_str(),
                "format":   item.format_id,
                "audio":    item.audio_only,
            })

    def _run_download(self, item: DownloadItem, on_progress: Optional[Callable]):
        """The actual yt-dlp call."""
        hook = _ProgressHook(item, on_progress)

        output_template = os.path.join(
            item.output_dir,
            "%(title)s [%(id)s].%(ext)s",
        )

        ydl_opts: dict = {
            "quiet":           True,
            "no_warnings":     True,
            "progress_hooks":  [hook],
            "outtmpl":         output_template,
            "noplaylist":      True,
            "retries":         0,           # we handle retries ourselves
            "continuedl":      True,        # resume partial downloads
            "noprogress":      False,
        }

        # ── Bundled ffmpeg location (when running as a frozen .exe) ────────
        import sys
        if getattr(sys, "frozen", False):
            # PyInstaller extracts bundled files to sys._MEIPASS at runtime
            _ffmpeg_dir = os.path.join(sys._MEIPASS, "ffmpeg")
            if os.path.isdir(_ffmpeg_dir):
                ydl_opts["ffmpeg_location"] = _ffmpeg_dir

        # ── Format selection ───────────────────────────────────────────────
        if item.audio_only:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key":             "FFmpegExtractAudio",
                "preferredcodec":  settings.get("audio_format", "mp3"),
                "preferredquality": settings.get("audio_quality", "192"),
            }]
        else:
            ydl_opts["format"] = item.format_id
            # Merge video+audio streams when separate
            ydl_opts["merge_output_format"] = "mp4"

        # Thumbnail download
        if settings.get("download_thumbnail"):
            ydl_opts["writethumbnail"] = True

        # Proxy / rate limit
        proxy = settings.get("proxy", "").strip()
        if proxy:
            ydl_opts["proxy"] = proxy
        rate  = settings.get("rate_limit", "").strip()
        if rate:
            ydl_opts["ratelimit"] = _parse_rate(rate)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([item.url])
            item.status   = DownloadStatus.COMPLETED
            item.progress = 100.0
        except yt_dlp.utils.DownloadCancelled:
            item.status = DownloadStatus.CANCELLED
            # Delete any .part / .ytdl temp files left on disk
            _cleanup_partial_files(item)
        except yt_dlp.utils.DownloadError as exc:
            item.status = DownloadStatus.FAILED
            item.error  = _clean_error(str(exc))
        except Exception as exc:
            item.status = DownloadStatus.FAILED
            item.error  = str(exc)


# ─────────────────────── Helpers ────────────────────────────────────────────

def _cleanup_partial_files(item: "DownloadItem"):
    """
    After a cancellation, remove any temporary / partial files that
    yt-dlp left behind in the output directory.

    yt-dlp uses extensions like:
      .part       – partial fragment
      .ytdl       – download state file
      .part-Frag* – DASH / HLS fragments
    """
    import glob
    output_dir = item.output_dir
    if not output_dir or not os.path.isdir(output_dir):
        return

    patterns = [
        os.path.join(output_dir, "*.part"),
        os.path.join(output_dir, "*.ytdl"),
        os.path.join(output_dir, "*.part-Frag*"),
    ]
    for pattern in patterns:
        for fpath in glob.glob(pattern):
            try:
                os.remove(fpath)
            except OSError:
                pass


def _parse_rate(rate_str: str) -> Optional[int]:
    """Convert '2M' / '500K' strings to bytes/s integers."""
    m = re.match(r'^(\d+(?:\.\d+)?)([KMG]?)$', rate_str.upper())
    if not m:
        return None
    value, unit = float(m.group(1)), m.group(2)
    return int(value * {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3}.get(unit, 1))


def _clean_error(msg: str) -> str:
    """Strip yt-dlp boilerplate from error messages."""
    msg = re.sub(r'^ERROR:\s*', '', msg, flags=re.IGNORECASE)
    return msg.strip()


def parse_formats(info: dict) -> List[Dict]:
    """
    Convert the 'formats' list from yt-dlp info_dict into clean dicts
    suitable for displaying in the format table.
    """
    results = []
    seen    = set()

    for fmt in info.get("formats", []):
        ext    = fmt.get("ext", "?")
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")

        has_video = vcodec not in (None, "none", "")
        has_audio = acodec not in (None, "none", "")

        height  = fmt.get("height")   or 0
        fps     = fmt.get("fps")      or 0
        tbr     = fmt.get("tbr")      or 0
        size    = fmt.get("filesize") or fmt.get("filesize_approx")
        fmt_id  = fmt.get("format_id", "")

        # Codec label
        if has_video and has_audio:
            codec_label = f"{_short_codec(vcodec)}+{_short_codec(acodec)}"
            stream_type = "Video+Audio"
        elif has_video:
            codec_label = _short_codec(vcodec)
            stream_type = "Video"
        else:
            codec_label = _short_codec(acodec)
            stream_type = "Audio"

        resolution = f"{height}p" if height else ("Audio" if not has_video else "?")

        key = (resolution, fps, codec_label, ext)
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "format_id":   fmt_id,
            "resolution":  resolution,
            "fps":         int(fps) if fps else 0,
            "codec":       codec_label,
            "size":        format_bytes(size) if size else "~",
            "size_bytes":  size or 0,
            "ext":         ext,
            "tbr":         tbr,
            "has_video":   has_video,
            "has_audio":   has_audio,
            "stream_type": stream_type,
        })

    # Sort: video+audio first, then by resolution desc
    def _sort_key(r):
        h = int(r["resolution"].replace("p", "")) if r["resolution"].endswith("p") else 0
        order = 0 if r["stream_type"] == "Video+Audio" else (1 if r["stream_type"] == "Video" else 2)
        return (order, -h, -(r["fps"] or 0))

    results.sort(key=_sort_key)
    return results


def _short_codec(codec: str) -> str:
    """Return a readable short codec label."""
    if not codec or codec == "none":
        return "–"
    if "avc1" in codec or "h264" in codec:
        return "H.264"
    if "vp9" in codec:
        return "VP9"
    if "av01" in codec:
        return "AV1"
    if "hvc1" in codec or "hevc" in codec:
        return "H.265"
    if "mp4a" in codec:
        return "AAC"
    if "opus" in codec:
        return "Opus"
    if "vorbis" in codec:
        return "Vorbis"
    return codec.split(".")[0].upper()


# Singleton
downloader = Downloader()
