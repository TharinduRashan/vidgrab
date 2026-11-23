"""
Automated Comprehensive Test Suite for VidGrab
=============================================
Covers unit tests, edge cases, state transitions, and integration for:
- utils.helpers
- utils.settings
- core.downloader
- ui.theme & ui.styles
- ui.widgets
- ui.download_panel
- ui.app
"""

import math
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import shutil
import tempfile
import threading
import time
import tkinter as tk
import pytest

from utils.helpers import (
    is_valid_url, is_playlist_url, format_bytes, format_speed,
    format_eta, format_duration, sanitize_filename, ensure_dir,
    short_id, now_str,
)
from utils.settings import Settings
from core.downloader import (
    DownloadItem, DownloadStatus, Downloader,
    _parse_rate, _clean_error, parse_formats, downloader
)
from ui.theme import theme_manager, COLORS, _DARK, _LIGHT
from ui.styles import apply_theme, refresh_treeview_tags
from ui.widgets import AnimatedProgressBar, StatusBadge, ScrollableFrame, Tooltip, SectionHeader
from ui.download_panel import DownloadCard, DownloadQueuePanel
from ui.app import YoutubeDownloaderApp


# ============================================================================
# 1. utils.helpers Tests
# ============================================================================

class TestHelpers:
    def test_is_valid_url(self):
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/abcdef12345",
            "https://www.youtube.com/live/abcdef12345",
            "https://www.youtube.com/embed/abcdef12345",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/playlist?list=PL1234567890",
            "https://www.facebook.com/watch/?v=1234567890",
            "https://www.instagram.com/reel/C34xyz123/",
            "https://x.com/user/status/1234567890123456789",
            "https://twitter.com/user/status/1234567890123456789",
            "https://www.tiktok.com/@user/video/1234567890123456789",
            "https://vimeo.com/123456789",
            "https://soundcloud.com/artist/track",
            "https://www.dailymotion.com/video/x7tgad0",
            "https://example.com/video.mp4",
        ]
        for url in valid_urls:
            assert is_valid_url(url) is True, f"Failed for valid URL: {url}"

        invalid_urls = [
            "",
            "   ",
            "not a url",
            "ftp://invalid.com/file",
            "javascript:void(0)",
            "file:///C:/path/to/file",
        ]
        for url in invalid_urls:
            assert is_valid_url(url) is False, f"Expected False for invalid URL: {url}"

    def test_is_playlist_url(self):
        assert is_playlist_url("https://www.youtube.com/playlist?list=PL123") is True
        assert is_playlist_url("https://music.youtube.com/playlist?list=PL123") is True
        assert is_playlist_url("https://www.youtube.com/watch?v=123") is False
        assert is_playlist_url("https://vimeo.com/123") is False

    def test_format_bytes(self):
        assert format_bytes(None) == "–"
        assert format_bytes("invalid") == "–"
        assert format_bytes(0) == "0 B"
        assert format_bytes(-50) == "0 B"
        assert format_bytes(500) == "500.0 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
        assert format_bytes(0.0001) == "0.0 B"

    def test_format_speed(self):
        assert format_speed(None) == "–"
        assert format_speed(1024 * 1024) == "1.0 MB/s"

    def test_format_eta(self):
        assert format_eta(None) == "–"
        assert format_eta(-5) == "–"
        assert format_eta(float("nan")) == "–"
        assert format_eta(float("inf")) == "–"
        assert format_eta(0) == "0:00"
        assert format_eta(45) == "0:45"
        assert format_eta(65) == "1:05"
        assert format_eta(3665) == "1:01:05"

    def test_format_duration(self):
        assert format_duration(None) == "–"
        assert format_duration(120) == "2:00"
        assert format_duration(3600) == "1:00:00"

    def test_sanitize_filename(self):
        assert sanitize_filename('test:file*name?with"bad/chars') == "test_file_name_with_bad_chars"
        assert sanitize_filename("...   ") == "download"
        assert sanitize_filename("") == "download"
        long_name = "a" * 250
        assert len(sanitize_filename(long_name, max_length=100)) == 100

    def test_short_id_and_now_str(self):
        sid = short_id("https://youtube.com/watch?v=123")
        assert len(sid) == 8
        now = now_str()
        assert len(now) == 19 and now[4] == "-" and now[7] == "-"


# ============================================================================
# 2. utils.settings Tests
# ============================================================================

class TestSettings:
    def test_settings_lifecycle(self, monkeypatch):
        temp_dir = tempfile.mkdtemp()
        try:
            import utils.settings as s_mod
            monkeypatch.setattr(s_mod, "_APP_DATA_DIR", temp_dir)
            monkeypatch.setattr(s_mod, "_SETTINGS_FILE", os.path.join(temp_dir, "settings.json"))

            s = Settings()
            assert s.get("concurrent_downloads") == 2
            s.set("concurrent_downloads", 4)
            assert s.get("concurrent_downloads") == 4

            # Reload from disk
            s2 = Settings()
            assert s2.get("concurrent_downloads") == 4

            # Reset
            s2.reset()
            assert s2.get("concurrent_downloads") == 2

            # History
            assert s2.load_history() == []
            s2.append_history({"title": "Test Video", "url": "https://youtu.be/123", "path": "test.mp4"})
            h = s2.load_history()
            assert len(h) == 1
            assert h[0]["title"] == "Test Video"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# 3. core.downloader Tests
# ============================================================================

class TestDownloader:
    def test_download_item_controls(self):
        item = DownloadItem(url="https://youtube.com/watch?v=123", title="Test")
        assert item.status == DownloadStatus.QUEUED
        assert not item.is_paused()
        assert not item.is_cancelled()

        item.pause()
        assert item.status == DownloadStatus.PAUSED
        assert item.is_paused()

        item.resume()
        assert item.status == DownloadStatus.ACTIVE
        assert not item.is_paused()

        item.cancel()
        assert item.status == DownloadStatus.CANCELLED
        assert item.is_cancelled()

    def test_parse_rate(self):
        assert _parse_rate("2M") == 2 * 1024 * 1024
        assert _parse_rate("500K") == 500 * 1024
        assert _parse_rate("1G") == 1024 * 1024 * 1024
        assert _parse_rate("invalid") is None

    def test_clean_error(self):
        assert _clean_error("ERROR: Video unavailable") == "Video unavailable"
        assert _clean_error("Generic error") == "Generic error"

    def test_parse_formats_robustness(self):
        assert parse_formats(None) == []
        assert parse_formats({}) == []
        dummy_info = {
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "vcodec": "avc1.42001E",
                    "acodec": "mp4a.40.2",
                    "height": 360,
                    "fps": 30,
                    "tbr": 450.0,
                    "filesize": 15000000,
                },
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "vcodec": "avc1.640028",
                    "acodec": "none",
                    "height": 1080.0,  # float height
                    "fps": 60.0,       # float fps
                    "tbr": 4000.5,
                    "filesize": 80000000,
                },
                {
                    "format_id": "251",
                    "ext": "webm",
                    "vcodec": "none",
                    "acodec": "opus",
                    "height": None,
                    "fps": None,
                    "tbr": 160.0,
                    "filesize": 5000000,
                },
            ]
        }
        fmts = parse_formats(dummy_info)
        assert len(fmts) == 3
        # First should be Video+Audio (format 18)
        assert fmts[0]["stream_type"] == "Video+Audio"
        assert fmts[0]["resolution"] == "360p"
        # Second should be 1080p Video-only (format 137)
        assert fmts[1]["stream_type"] == "Video"
        assert fmts[1]["resolution"] == "1080p"
        assert fmts[1]["height"] == 1080
        # Third should be Audio (format 251)
        assert fmts[2]["stream_type"] == "Audio"
        assert fmts[2]["resolution"] == "Audio"

    def test_downloader_concurrency(self):
        dl = Downloader()
        dl.set_concurrency(4)
        assert dl._concurrent_limit == 4


# ============================================================================
# 4. ui.theme & ui.styles Tests
# ============================================================================

class TestThemeAndStyles:
    def test_theme_toggle(self):
        root = tk.Tk()
        try:
            assert theme_manager.is_dark is True
            old_c, new_c = theme_manager.toggle()
            assert theme_manager.is_dark is False
            assert COLORS["mode"] == "light"

            apply_theme(root)
            theme_manager.retheme_all(root, old_c, new_c)

            # Toggle back to dark
            old_c2, new_c2 = theme_manager.toggle()
            assert theme_manager.is_dark is True
            assert COLORS["mode"] == "dark"
            apply_theme(root)
            theme_manager.retheme_all(root, old_c2, new_c2)
        finally:
            root.destroy()


# ============================================================================
# 5. ui.widgets Tests
# ============================================================================

class TestWidgets:
    def test_widgets_creation(self):
        root = tk.Tk()
        try:
            apply_theme(root)
            # AnimatedProgressBar
            pbar = AnimatedProgressBar(root)
            pbar.pack()
            pbar.set(50)
            assert pbar._value.get() == 50.0
            pbar.set(100)
            assert pbar._value.get() == 100.0

            # StatusBadge
            badge = StatusBadge(root, status="ACTIVE")
            badge.pack()
            assert badge.cget("text") == " ACTIVE "
            badge.set_status("COMPLETED")
            assert badge.cget("text") == " COMPLETED "

            # SectionHeader
            hdr = SectionHeader(root, title="Test Section")
            hdr.pack()

            # Tooltip
            lbl = tk.Label(root, text="Hover me")
            lbl.pack()
            tt = Tooltip(lbl, "Tooltip text")
            assert tt._text == "Tooltip text"

            # ScrollableFrame
            sf = ScrollableFrame(root)
            sf.pack(fill="both", expand=True)
            tk.Label(sf.inner, text="Inner Content").pack()

            root.update()
        finally:
            root.destroy()


# ============================================================================
# 6. ui.download_panel Tests
# ============================================================================

class TestDownloadPanel:
    def test_queue_panel_lifecycle(self):
        root = tk.Tk()
        try:
            apply_theme(root)
            panel = DownloadQueuePanel(root)
            panel.pack(fill="both", expand=True)

            item1 = DownloadItem(url="https://youtube.com/watch?v=abc", title="Item 1")
            item2 = DownloadItem(url="https://youtube.com/watch?v=def", title="Item 2")

            card1 = panel.add_item(item1)
            card2 = panel.add_item(item2)
            assert len(panel._cards) == 2

            # Update item states
            item1.status = DownloadStatus.ACTIVE
            item1.progress = 45.0
            item1.speed = 1024 * 1024
            item1.eta = 30
            panel.update_item(item1)
            root.update()

            item1.status = DownloadStatus.COMPLETED
            item1.progress = 100.0
            panel.update_item(item1)
            root.update()
            assert card1._folder_btn.winfo_ismapped()

            # Remove completed
            panel.remove_completed()
            assert len(panel._cards) == 1

            # Clear all
            panel.clear_all()
            assert len(panel._cards) == 0
        finally:
            root.destroy()


# ============================================================================
# 7. ui.app Integration Tests
# ============================================================================

class TestAppIntegration:
    def test_app_initialization_and_formats(self):
        app = YoutubeDownloaderApp()
        try:
            # Check tabs exist
            assert hasattr(app, "_notebook")
            assert hasattr(app, "_info_tab")
            assert hasattr(app, "_playlist_tab")

            # Simulate fetching video info
            dummy_info = {
                "title": "Integration Test Video",
                "uploader": "Test Channel",
                "duration": 300,
                "view_count": 123456,
                "thumbnail": "",
                "formats": [
                    {"format_id": "18", "ext": "mp4", "vcodec": "avc1", "acodec": "mp4a", "height": 360, "fps": 30, "filesize": 1000000},
                    {"format_id": "137", "ext": "mp4", "vcodec": "avc1", "acodec": "none", "height": 1080, "fps": 60, "filesize": 5000000},
                ],
            }
            app._active_fetch_id = 1
            app._on_info_fetched(dummy_info, 1)
            assert app._title_var.get() == "Integration Test Video"
            assert app._channel_var.get() == "Test Channel"
            assert len(app._fmt_tree.get_children()) == 2

            # Test format column sorting
            app._sort_formats("Resolution")
            assert app._sort_col == "Resolution"
            app._sort_formats("Resolution")
            assert app._sort_rev is False

            # Simulate fetching playlist
            dummy_playlist = {
                "title": "Integration Playlist",
                "entries": [
                    {"title": "Track 1", "duration": 180, "url": "https://youtu.be/1"},
                    {"title": "Track 2", "duration": 210, "url": "https://youtu.be/2"},
                ],
            }
            app._on_playlist_fetched(dummy_playlist, 1)
            assert app._playlist_title_var.get() == "Integration Playlist"
            assert len(app._pl_tree.get_children()) == 2

            # Test cancel fetch
            app._is_fetching = True
            app._cancel_fetch()
            assert app._is_fetching is False
            assert app._fetch_btn.cget("text") == "Fetch"

            # Test clear info
            app._clear_info()
            assert app._title_var.get() == "–"
            assert len(app._fmt_tree.get_children()) == 0

            app._root.update()
        finally:
            app._root.destroy()
