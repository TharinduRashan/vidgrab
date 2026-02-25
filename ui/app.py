"""
Main Application Window
=======================
Assembles all UI panels and wires them to the core download engine.

Layout (horizontal split):
  ┌──────────────────────────────┬─────────────────────┐
  │  Left: URL + Info + Formats  │  Right: Queue Panel  │
  └──────────────────────────────┴─────────────────────┘
"""

import io
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional

# Pillow (optional – graceful fallback)
try:
    from PIL import Image, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

from core.downloader import (
    DownloadItem, DownloadStatus, downloader, parse_formats
)
from ui.download_panel import DownloadQueuePanel
from ui.history_dialog import HistoryDialog
from ui.settings_dialog import SettingsDialog
from ui.styles import apply_theme, refresh_treeview_tags
from ui.theme import COLORS as C, FONTS as F, DIMENSIONS as D, theme_manager
from utils.helpers import (
    format_bytes, format_duration, is_playlist_url, is_valid_url,
    is_valid_youtube_url, default_download_folder,
)
from utils.settings import settings


class YoutubeDownloaderApp:
    """Root application controller."""

    def __init__(self):
        self._root        = tk.Tk()
        self._root.title("VidGrab")
        self._root.geometry(f"{D['window_width']}x{D['window_height']}")
        self._root.minsize(D["min_width"], D["min_height"])

        # Start maximised so all panels are immediately visible
        try:
            self._root.state("zoomed")   # Windows maximise
        except Exception:
            try:
                self._root.attributes("-zoomed", True)  # Linux/macOS fallback
            except Exception:
                pass

        # Restore saved theme preference BEFORE building the UI
        saved_mode = settings.get("theme", "dark")
        if saved_mode != theme_manager.mode:
            theme_manager.set_mode(saved_mode)   # update COLORS in-place only

        apply_theme(self._root)
        self._set_icon()

        # State
        self._current_info:    Optional[dict]         = None
        self._current_formats: List[dict]             = []
        self._thumb_photo:     Optional[tk.PhotoImage] = None
        self._playlist_items:  List[dict]             = []
        self._dl_folder        = tk.StringVar(value=settings.get("download_folder"))
        self._audio_only       = tk.BooleanVar(value=False)
        self._url_var          = tk.StringVar()
        self._status_var       = tk.StringVar(value="Ready")

        self._build_ui()
        self._bind_drag_drop()

    # ── Icon ───────────────────────────────────────────────────────────────

    def _set_icon(self):
        """Attempt to set window icon (optional)."""
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
        if os.path.isfile(icon_path):
            try:
                self._root.iconbitmap(icon_path)
            except Exception:
                pass

    # ────────────────────────────── UI LAYOUT ─────────────────────────────

    def _build_ui(self):
        self._build_titlebar()
        self._build_main_panes()
        self._build_statusbar()

    # ── Title bar ──────────────────────────────────────────────────────────

    def _build_titlebar(self):
        bar = ttk.Frame(self._root, style="Dark.TFrame", padding=(16, 10, 16, 10))
        bar.pack(fill="x")

        # Logo / title
        title_frame = ttk.Frame(bar, style="Dark.TFrame")
        title_frame.pack(side="left")

        tk.Label(title_frame, text="↓",
                 fg=C["accent"], bg=C["bg_primary"],
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(title_frame, text="  VidGrab",
                 fg=C["text_primary"], bg=C["bg_primary"],
                 font=("Segoe UI", 18, "bold")).pack(side="left")

        # Platform support chips
        chips_frame = ttk.Frame(bar, style="Dark.TFrame")
        chips_frame.pack(side="left", padx=(16, 0))
        for chip_text, chip_fg, chip_bg in [
            ("YouTube",   "#FFFFFF", "#FF0000"),
            ("Facebook",  "#FFFFFF", "#1877F2"),
            ("Instagram", "#FFFFFF", "#C13584"),
            ("TikTok",    "#FFFFFF", "#010101"),
            ("+ more",    C["text_muted"], C["bg_tertiary"]),
        ]:
            tk.Label(
                chips_frame, text=chip_text,
                bg=chip_bg, fg=chip_fg,
                font=("Segoe UI", 8, "bold"),
                padx=6, pady=2, relief="flat",
            ).pack(side="left", padx=2)

        # Right-side actions
        btn_frame = ttk.Frame(bar, style="Dark.TFrame")
        btn_frame.pack(side="right")

        # Theme toggle button
        self._theme_btn = tk.Button(
            btn_frame,
            text="☀  Light Mode" if theme_manager.is_dark else "🌙  Dark Mode",
            command=self._toggle_theme,
            bg=C["bg_hover"], fg=C["accent"],
            relief="flat", font=F["small"], padx=12, pady=6,
            cursor="hand2",
            activebackground=C["bg_selected"],
            activeforeground=C["accent"],
        )
        self._theme_btn.pack(side="left", padx=4)

        for (text, cmd) in [
            ("🕐 History", self._open_history),
            ("⚙ Settings", self._open_settings),
        ]:
            tk.Button(
                btn_frame, text=text, command=cmd,
                bg=C["bg_hover"], fg=C["text_secondary"],
                relief="flat", font=F["small"], padx=12, pady=6,
                cursor="hand2",
                activebackground=C["bg_selected"],
                activeforeground=C["text_primary"],
            ).pack(side="left", padx=4)

        ttk.Separator(self._root, orient="horizontal").pack(fill="x")

    # ── Main panes ─────────────────────────────────────────────────────────

    def _build_main_panes(self):
        """Horizontal PanedWindow: left=search+info+formats, right=queue."""
        pw = tk.PanedWindow(
            self._root, orient="horizontal",
            bg=C["border"], sashwidth=4, sashrelief="flat",
            handlesize=0,
        )
        pw.pack(fill="both", expand=True)

        # ── Left panel ────────────────────────────────────────────
        left = ttk.Frame(pw, style="Dark.TFrame")
        pw.add(left, minsize=520, width=680)
        self._build_left_panel(left)

        # ── Right panel (queue) ───────────────────────────────────
        right = ttk.Frame(pw, style="Dark.TFrame")
        pw.add(right, minsize=340)
        self._queue_panel = DownloadQueuePanel(right)
        self._queue_panel.pack(fill="both", expand=True)

    # ── Left panel ─────────────────────────────────────────────────────────

    def _build_left_panel(self, parent):
        # URL search row
        self._build_url_row(parent)

        # Info + formats (tabbed)
        notebook = ttk.Notebook(parent, style="Dark.TNotebook")
        notebook.pack(fill="both", expand=True, padx=12, pady=8)

        # Tab 1: Video info + format selector
        self._info_tab = ttk.Frame(notebook, style="Dark.TFrame")
        notebook.add(self._info_tab, text="  Video Info  ")
        self._build_info_tab(self._info_tab)

        # Tab 2: Playlist viewer
        self._playlist_tab = ttk.Frame(notebook, style="Dark.TFrame")
        notebook.add(self._playlist_tab, text="  Playlist  ")
        self._build_playlist_tab(self._playlist_tab)

    # ── URL row ────────────────────────────────────────────────────────────

    def _build_url_row(self, parent):
        row = ttk.Frame(parent, style="Dark.TFrame", padding=(12, 12, 12, 6))
        row.pack(fill="x")

        # URL entry
        url_frame = ttk.Frame(row, style="Dark.TFrame")
        url_frame.pack(fill="x", pady=(0, 8))

        tk.Label(url_frame,
                 text="Paste a URL from YouTube, Facebook, Instagram, TikTok, Vimeo, Twitter…",
                 fg=C["text_muted"],
                 bg=C["bg_primary"], font=F["small"]).pack(anchor="w")

        entry_row = ttk.Frame(url_frame, style="Dark.TFrame")
        entry_row.pack(fill="x")

        self._url_entry = tk.Entry(
            entry_row,
            textvariable=self._url_var,
            bg=C["bg_tertiary"], fg=C["text_primary"],
            insertbackground=C["text_primary"],
            relief="flat", font=F["url"],
            highlightthickness=1,
            highlightcolor=C["accent"],
            highlightbackground=C["border"],
        )
        self._url_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        self._url_entry.bind("<Return>", lambda _: self._fetch_info())

        # Paste button
        tk.Button(
            entry_row, text="📋",
            bg=C["bg_hover"], fg=C["text_secondary"],
            relief="flat", font=F["body"], padx=8, pady=8,
            cursor="hand2", command=self._paste_url,
            activebackground=C["bg_selected"],
        ).pack(side="left", padx=(0, 6))

        # Search/Fetch button
        self._fetch_btn = tk.Button(
            entry_row, text="Fetch",
            bg=C["accent"], fg="#FFFFFF",
            relief="flat", font=F["body_bold"], padx=18, pady=8,
            cursor="hand2", command=self._fetch_info,
            activebackground=C["accent_dark"],
        )
        self._fetch_btn.pack(side="left")

        # ── Download controls row ──────────────────────────────────
        ctrl = ttk.Frame(row, style="Dark.TFrame")
        ctrl.pack(fill="x")

        # Download folder
        folder_frame = ttk.Frame(ctrl, style="Dark.TFrame")
        folder_frame.pack(side="left", fill="x", expand=True)

        tk.Label(folder_frame, text="Save to:", fg=C["text_muted"],
                 bg=C["bg_primary"], font=F["small"]).pack(side="left")

        self._folder_label = tk.Label(
            folder_frame, textvariable=self._dl_folder,
            fg=C["accent_blue"], bg=C["bg_primary"],
            font=F["small"], cursor="hand2",
        )
        self._folder_label.pack(side="left", padx=(6, 0))
        self._folder_label.bind("<Button-1>", lambda _: self._browse_folder())

        tk.Button(
            folder_frame, text="…",
            bg=C["bg_hover"], fg=C["text_secondary"],
            relief="flat", font=F["small"], padx=6, pady=3,
            cursor="hand2", command=self._browse_folder,
        ).pack(side="left", padx=(4, 0))

        # Audio-only toggle
        ttk.Checkbutton(
            ctrl, text="Audio only (MP3)",
            variable=self._audio_only,
        ).pack(side="right", padx=(8, 0))

    # ── Info tab ───────────────────────────────────────────────────────────

    def _build_info_tab(self, parent):
        # Outer pane: thumbnail left, meta right
        top = ttk.Frame(parent, style="Dark.TFrame", padding=12)
        top.pack(fill="x")

        # Thumbnail
        self._thumb_canvas = tk.Canvas(
            top, width=D["thumbnail_width"], height=D["thumbnail_height"],
            bg=C["bg_secondary"], highlightthickness=0,
        )
        self._thumb_canvas.pack(side="left")
        self._thumb_canvas.create_text(
            D["thumbnail_width"] // 2, D["thumbnail_height"] // 2,
            text="No Preview", fill=C["text_muted"], font=F["small"],
        )

        # Meta info (right of thumbnail)
        meta = ttk.Frame(top, style="Dark.TFrame", padding=(12, 0, 0, 0))
        meta.pack(side="left", fill="both", expand=True)

        self._title_var    = tk.StringVar(value="–")
        self._channel_var  = tk.StringVar(value="–")
        self._duration_var = tk.StringVar(value="–")
        self._views_var    = tk.StringVar(value="–")

        for label, var in [
            ("Title",    self._title_var),
            ("Channel",  self._channel_var),
            ("Duration", self._duration_var),
            ("Views",    self._views_var),
        ]:
            r = ttk.Frame(meta, style="Dark.TFrame")
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"{label}:", fg=C["text_muted"],
                     bg=C["bg_primary"], font=F["small"], width=9, anchor="e").pack(side="left")
            tk.Label(r, textvariable=var, fg=C["text_primary"],
                     bg=C["bg_primary"], font=F["body"], wraplength=340, anchor="w",
                     justify="left").pack(side="left", padx=(6, 0))

        # ── Format table ───────────────────────────────────────────
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=12)

        fmt_header = ttk.Frame(parent, style="Dark.TFrame", padding=(12, 8, 12, 4))
        fmt_header.pack(fill="x")
        tk.Label(fmt_header, text="Available Formats",
                 fg=C["text_primary"], bg=C["bg_primary"],
                 font=F["subheading"]).pack(side="left")
        tk.Label(fmt_header, text="Select a row then click Download",
                 fg=C["text_muted"], bg=C["bg_primary"], font=F["small"]).pack(side="left", padx=12)

        # Treeview
        cols = ("Resolution", "FPS", "Codec", "Size", "Type", "Format ID")
        tree_frame = ttk.Frame(parent, style="Dark.TFrame", padding=(12, 0, 12, 0))
        tree_frame.pack(fill="both", expand=True)

        self._fmt_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Dark.Treeview", selectmode="browse", height=10,
        )
        col_widths = {"Resolution": 90, "FPS": 60, "Codec": 100, "Size": 80, "Type": 90, "Format ID": 90}
        for col in cols:
            self._fmt_tree.heading(col, text=col, command=lambda c=col: self._sort_formats(c))
            self._fmt_tree.column(col, width=col_widths.get(col, 80), anchor="center", minwidth=50)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._fmt_tree.yview,
                             style="Dark.Vertical.TScrollbar")
        self._fmt_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._fmt_tree.pack(side="left", fill="both", expand=True)

        # Alternating row colours
        self._fmt_tree.tag_configure("odd",  background=C["bg_tertiary"])
        self._fmt_tree.tag_configure("even", background=C["bg_secondary"])
        self._fmt_tree.tag_configure("best", background="#1A2B1A")  # highlight best quality

        dl_row = ttk.Frame(parent, style="Dark.TFrame", padding=(12, 10))
        dl_row.pack(fill="x")

        self._dl_btn = tk.Button(
            dl_row, text="⬇  Download Selected",
            bg=C["accent"], fg="#FFFFFF",
            relief="flat", font=F["body_bold"], padx=20, pady=10,
            cursor="hand2", command=self._start_download,
            activebackground=C["accent_dark"],
            disabledforeground="#6B8FD4",
            state="disabled",
        )
        self._dl_btn.pack(side="left")

        tk.Button(
            dl_row, text="⬇  Best Quality",
            bg="#16A34A", fg="#FFFFFF",
            relief="flat", font=F["body_bold"], padx=20, pady=10,
            cursor="hand2", command=self._download_best,
            activebackground="#15803D",
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            dl_row, text="+ Add to Queue",
            bg=C["bg_tertiary"], fg=C["text_primary"],
            relief="flat", font=F["body_bold"], padx=14, pady=10,
            cursor="hand2", command=lambda: self._start_download(use_best=True),
            activebackground=C["bg_hover"],
        ).pack(side="right")

    # ── Playlist tab ────────────────────────────────────────────────────────

    def _build_playlist_tab(self, parent):
        header = ttk.Frame(parent, style="Dark.TFrame", padding=(12, 8))
        header.pack(fill="x")
        self._playlist_title_var = tk.StringVar(value="No playlist loaded")
        tk.Label(header, textvariable=self._playlist_title_var,
                 fg=C["text_primary"], bg=C["bg_primary"], font=F["subheading"]).pack(side="left")
        self._pl_count_var = tk.StringVar(value="")
        tk.Label(header, textvariable=self._pl_count_var,
                 fg=C["text_muted"], bg=C["bg_primary"], font=F["small"]).pack(side="left", padx=8)

        ttk.Separator(parent).pack(fill="x")

        pl_cols = ("#", "Title", "Duration", "URL")
        pf = ttk.Frame(parent, style="Dark.TFrame", padding=(12, 8))
        pf.pack(fill="both", expand=True)

        self._pl_tree = ttk.Treeview(
            pf, columns=pl_cols, show="headings",
            style="Dark.Treeview", selectmode="extended",
        )
        for col, width in zip(pl_cols, [40, 400, 80, 200]):
            self._pl_tree.heading(col, text=col)
            self._pl_tree.column(col, width=width, anchor="w", minwidth=30)

        vsb2 = ttk.Scrollbar(pf, orient="vertical",
                              command=self._pl_tree.yview,
                              style="Dark.Vertical.TScrollbar")
        self._pl_tree.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")
        self._pl_tree.pack(side="left", fill="both", expand=True)

        # Tag for alt rows
        self._pl_tree.tag_configure("odd",  background=C["bg_tertiary"])
        self._pl_tree.tag_configure("even", background=C["bg_secondary"])

        # Buttons
        btn_row = ttk.Frame(parent, style="Dark.TFrame", padding=(12, 6))
        btn_row.pack(fill="x")

        tk.Button(
            btn_row, text="⬇ Download Selected",
            bg=C["accent"], fg="#FFFFFF",
            relief="flat", font=F["body_bold"], padx=14, pady=8,
            cursor="hand2", command=self._download_playlist_selected,
        ).pack(side="left")

        tk.Button(
            btn_row, text="⬇ Download All",
            bg="#1D4ED8", fg="#FFFFFF",
            relief="flat", font=F["body_bold"], padx=14, pady=8,
            cursor="hand2", command=self._download_playlist_all,
        ).pack(side="left", padx=(8, 0))

    # ── Status bar ─────────────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = ttk.Frame(self._root, style="Dark.TFrame", padding=(12, 4))
        bar.pack(fill="x", side="bottom")
        ttk.Separator(self._root, orient="horizontal").pack(fill="x", side="bottom")
        ttk.Label(bar, textvariable=self._status_var,
                  style="Muted.TLabel").pack(side="left")
        ttk.Label(bar, text="yt-dlp powered  ·  YT Downloader Pro",
                  style="Muted.TLabel").pack(side="right")

    # ────────────────────────── ACTIONS ────────────────────────────────────

    def _paste_url(self):
        try:
            text = self._root.clipboard_get()
            self._url_var.set(text.strip())
        except tk.TclError:
            pass

    def _browse_folder(self):
        folder = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self._dl_folder.get() or default_download_folder(),
        )
        if folder:
            self._dl_folder.set(folder)
            settings.set("download_folder", folder)

    # ── Fetch video info ───────────────────────────────────────────────────

    def _fetch_info(self):
        url = self._url_var.get().strip()
        if not url:
            self._show_error("Please enter a URL.")
            return
        if not is_valid_url(url):
            self._show_error("Unsupported URL.\n\nSupported platforms: YouTube, Facebook, Instagram, TikTok, Vimeo, Twitter/X, Reddit, Twitch, and more.")
            return

        self._status_var.set("Fetching video info…")
        self._fetch_btn.configure(state="disabled", text="⏳ Fetching…")
        self._dl_btn.configure(state="disabled")
        self._clear_info()

        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url: str):
        try:
            if is_playlist_url(url):
                info = downloader.fetch_info(url)
                self._root.after(0, self._on_playlist_fetched, info)
            else:
                info = downloader.fetch_formats(url)
                self._root.after(0, self._on_info_fetched, info)
        except Exception as exc:
            self._root.after(0, self._on_fetch_error, str(exc))

    def _on_info_fetched(self, info: dict):
        self._current_info    = info
        self._current_formats = parse_formats(info)

        self._title_var.set(info.get("title", "Unknown")[:80])
        self._channel_var.set(info.get("uploader", "Unknown"))
        self._duration_var.set(format_duration(info.get("duration")))
        views = info.get("view_count")
        self._views_var.set(f"{views:,}" if views else "–")

        self._populate_formats(self._current_formats)
        self._dl_btn.configure(state="normal")
        self._status_var.set(f"Loaded: {info.get('title', '')[:60]}")
        self._fetch_btn.configure(state="normal", text="🔍  Fetch Info")

        # Thumbnail
        thumb_url = info.get("thumbnail")
        if thumb_url:
            threading.Thread(target=self._load_thumbnail,
                             args=(thumb_url,), daemon=True).start()

    def _on_playlist_fetched(self, info: dict):
        entries = info.get("entries", []) or []
        self._playlist_items = [e for e in entries if e]

        title = info.get("title", "Playlist")
        self._playlist_title_var.set(title[:60])
        self._pl_count_var.set(f"({len(self._playlist_items)} videos)")

        self._pl_tree.delete(*self._pl_tree.get_children())
        for i, entry in enumerate(self._playlist_items):
            tag = "odd" if i % 2 else "even"
            dur = format_duration(entry.get("duration"))
            self._pl_tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                i + 1,
                entry.get("title") or entry.get("url", "")[:60],
                dur,
                entry.get("url") or entry.get("webpage_url", ""),
            ))

        self._status_var.set(f"Playlist loaded: {len(self._playlist_items)} videos")
        self._fetch_btn.configure(state="normal", text="🔍  Fetch Info")

    def _on_fetch_error(self, error: str):
        self._fetch_btn.configure(state="normal", text="🔍  Fetch Info")
        self._status_var.set("Failed to fetch info.")
        self._show_error(f"Could not fetch video info:\n\n{error[:200]}")

    def _clear_info(self):
        self._title_var.set("–")
        self._channel_var.set("–")
        self._duration_var.set("–")
        self._views_var.set("–")
        self._fmt_tree.delete(*self._fmt_tree.get_children())
        self._thumb_canvas.delete("all")
        self._thumb_canvas.create_text(
            D["thumbnail_width"] // 2, D["thumbnail_height"] // 2,
            text="Loading…", fill=C["text_muted"], font=F["small"],
        )

    # ── Thumbnail ──────────────────────────────────────────────────────────

    def _load_thumbnail(self, url: str):
        if not _PIL_AVAILABLE:
            return
        try:
            import requests
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))
            img = img.resize(
                (D["thumbnail_width"], D["thumbnail_height"]),
                Image.LANCZOS,
            )
            photo = ImageTk.PhotoImage(img)
            self._root.after(0, self._set_thumbnail, photo)
        except Exception:
            pass

    def _set_thumbnail(self, photo):
        self._thumb_photo = photo
        self._thumb_canvas.delete("all")
        self._thumb_canvas.create_image(0, 0, anchor="nw", image=photo)

    # ── Format table ──────────────────────────────────────────────────────

    def _populate_formats(self, formats: List[dict]):
        self._fmt_tree.delete(*self._fmt_tree.get_children())
        for i, fmt in enumerate(formats):
            tag = "best" if i == 0 else ("odd" if i % 2 else "even")
            self._fmt_tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                fmt["resolution"],
                f"{fmt['fps']} fps" if fmt["fps"] else "–",
                fmt["codec"],
                fmt["size"],
                fmt["stream_type"],
                fmt["format_id"],
            ))

        # Auto-select top row (best quality)
        if formats:
            self._fmt_tree.selection_set("0")
            self._fmt_tree.see("0")

    def _sort_formats(self, col: str):
        """Sort the formats treeview by column header click."""
        pass  # Could implement sorting; formats are already sorted by quality

    # ── Downloads ──────────────────────────────────────────────────────────

    def _start_download(self, use_best: bool = False):
        if not self._current_info:
            self._show_error("Please fetch video info first.")
            return

        if use_best or self._audio_only.get():
            fmt_id = "bestvideo+bestaudio/best"
        else:
            sel = self._fmt_tree.selection()
            if not sel:
                self._show_error("Please select a format from the table.")
                return
            row_idx = int(sel[0])
            if row_idx >= len(self._current_formats):
                return
            fmt     = self._current_formats[row_idx]
            fmt_id  = fmt["format_id"]
            # If video-only track → merge with best audio
            if not fmt["has_audio"] and fmt["has_video"]:
                fmt_id = f"{fmt_id}+bestaudio/best"

        item = DownloadItem(
            url        = self._current_info.get("webpage_url") or self._url_var.get().strip(),
            title      = self._current_info.get("title", "Unknown"),
            format_id  = fmt_id,
            audio_only = self._audio_only.get(),
            output_dir = self._dl_folder.get(),
            thumbnail_url = self._current_info.get("thumbnail", ""),
        )
        self._enqueue(item)

    def _download_best(self):
        self._start_download(use_best=True)

    def _download_playlist_selected(self):
        sel = self._pl_tree.selection()
        if not sel:
            self._show_error("Please select one or more playlist items.")
            return
        for iid in sel:
            idx  = int(iid)
            self._enqueue_playlist_item(idx)

    def _download_playlist_all(self):
        for idx in range(len(self._playlist_items)):
            self._enqueue_playlist_item(idx)

    def _enqueue_playlist_item(self, idx: int):
        entry = self._playlist_items[idx]
        url   = entry.get("url") or entry.get("webpage_url", "")
        if not url:
            return
        item = DownloadItem(
            url        = url,
            title      = entry.get("title") or url[:50],
            format_id  = "bestvideo+bestaudio/best",
            audio_only = self._audio_only.get(),
            output_dir = self._dl_folder.get(),
        )
        self._enqueue(item)

    def _enqueue(self, item: DownloadItem):
        """Add item to queue panel and start downloading."""
        card = self._queue_panel.add_item(item)
        self._status_var.set(f"Queued: {item.title[:50]}")

        def on_progress(it: DownloadItem):
            self._root.after(0, self._queue_panel.update_item, it)

        def on_done(it: DownloadItem):
            self._root.after(0, self._on_download_done, it)

        downloader.enqueue(item, on_progress=on_progress, on_done=on_done)

    def _on_download_done(self, item: DownloadItem):
        self._queue_panel.update_item(item)
        if item.status == DownloadStatus.COMPLETED:
            self._status_var.set(f"✓ Completed: {item.title[:50]}")
            if settings.get("open_folder_when_done"):
                folder = item.output_dir
                if item.filepath and os.path.isfile(item.filepath):
                    folder = os.path.dirname(item.filepath)
                if os.path.isdir(folder):
                    subprocess.Popen(f'explorer "{folder}"')
        elif item.status == DownloadStatus.FAILED:
            self._status_var.set(f"✗ Failed: {item.title[:50]}")

    # ── Drag and Drop (URL) ────────────────────────────────────────────────

    def _bind_drag_drop(self):
        """Attempt to register drag-drop (requires tkinterdnd2)."""
        try:
            from tkinterdnd2 import DND_TEXT
            self._url_entry.drop_target_register(DND_TEXT)
            self._url_entry.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass  # tkinterdnd2 not installed → skip silently

    def _on_drop(self, event):
        text = event.data.strip().strip("{}")
        self._url_var.set(text)
        self._root.after(100, self._fetch_info)

    # ── Dialogs ────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        """Switch between dark and light mode, repaint all widgets."""
        old_colors, new_colors = theme_manager.toggle()

        # 1. Re-apply all TTK styles
        apply_theme(self._root)

        # 2. Walk widget tree and swap palette colours on raw tk widgets
        theme_manager.retheme_all(self._root, old_colors, new_colors)

        # 3. Re-configure the root background (TTK won't do this)
        self._root.configure(bg=C["bg_primary"])

        # 4. Update treeview alternating-row tags
        refresh_treeview_tags(self._fmt_tree)
        refresh_treeview_tags(self._pl_tree)

        # 5. Update thumbnail canvas background
        self._thumb_canvas.configure(bg=C["bg_secondary"])

        # 6. Update toggle button label
        self._theme_btn.configure(
            text="☀  Light Mode" if theme_manager.is_dark else "🌙  Dark Mode"
        )

        # 7. Persist preference
        settings.set("theme", theme_manager.mode)

    def _open_settings(self):
        SettingsDialog(self._root)

    def _open_history(self):
        HistoryDialog(self._root)

    def _show_error(self, message: str):
        messagebox.showerror("Error", message, parent=self._root)

    # ── Entry point ────────────────────────────────────────────────────────

    def run(self):
        """Start the Tkinter event loop."""
        self._root.mainloop()
