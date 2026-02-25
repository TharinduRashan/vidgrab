"""
Settings Manager
================
Persistent JSON-based settings with sensible defaults.
"""

import json
import os
from utils.helpers import default_download_folder, ensure_dir

# Settings file lives in %APPDATA%\YTDownloader\settings.json
_APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "YTDownloader")
_SETTINGS_FILE = os.path.join(_APP_DATA_DIR, "settings.json")

_DEFAULTS = {
    "download_folder":      default_download_folder(),
    "concurrent_downloads": 2,
    "theme":                "dark",
    "audio_format":         "mp3",
    "audio_quality":        "192",
    "open_folder_when_done": True,
    "save_history":         True,
    "auto_retry":           True,
    "retry_count":          3,
    "download_thumbnail":   False,
    "preferred_quality":    "best",
    "proxy":                "",
    "rate_limit":           "",          # e.g. "2M" for 2 MB/s
}


class Settings:
    """Thread-safe JSON settings store."""

    def __init__(self):
        ensure_dir(_APP_DATA_DIR)
        self._data: dict = {}
        self.load()

    # ── Public API ─────────────────────────────────────────────────────────

    def get(self, key: str, fallback=None):
        """Return the setting value for *key*, or *fallback* if absent."""
        return self._data.get(key, _DEFAULTS.get(key, fallback))

    def set(self, key: str, value) -> None:
        """Update *key* in memory and persist to disk."""
        self._data[key] = value
        self.save()

    def update(self, mapping: dict) -> None:
        """Bulk-update several keys at once."""
        self._data.update(mapping)
        self.save()

    def reset(self) -> None:
        """Restore all settings to their default values."""
        self._data = dict(_DEFAULTS)
        self.save()

    # ── Persistence ────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load settings from disk; fall back to defaults if file missing."""
        if os.path.isfile(_SETTINGS_FILE):
            try:
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data = {**_DEFAULTS, **loaded}
                return
            except (json.JSONDecodeError, OSError):
                pass
        self._data = dict(_DEFAULTS)

    def save(self) -> None:
        """Persist current settings to disk."""
        try:
            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass  # Non-fatal – settings just won't persist

    # ── History ────────────────────────────────────────────────────────────

    @property
    def history_file(self) -> str:
        return os.path.join(_APP_DATA_DIR, "history.json")

    def load_history(self) -> list:
        if not os.path.isfile(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def append_history(self, entry: dict) -> None:
        """Append one download record to the history file."""
        if not self.get("save_history"):
            return
        history = self.load_history()
        history.insert(0, entry)
        history = history[:500]       # keep at most 500 records
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except OSError:
            pass


# Singleton instance used throughout the app
settings = Settings()
