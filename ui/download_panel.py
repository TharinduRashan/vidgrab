"""
Download Queue Panel
====================
Left-side panel that shows queued / active / completed download cards.
Each card displays a thumbnail, title, progress bar, speed, ETA, and
pause/resume/cancel controls.
"""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional

from core.downloader import DownloadItem, DownloadStatus
from ui.theme import COLORS as C, FONTS as F
from ui.widgets import AnimatedProgressBar, StatusBadge, ScrollableFrame
from utils.helpers import format_speed, format_eta


class DownloadCard(ttk.Frame):
    """
    One card in the download queue showing progress for a single item.
    """

    def __init__(self, parent, item: DownloadItem, on_pause_resume: Callable,
                 on_cancel: Callable, on_open_folder: Callable, on_remove: Callable, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self.item            = item
        self._on_pause_resume = on_pause_resume
        self._on_cancel       = on_cancel
        self._on_open_folder  = on_open_folder
        self._on_remove       = on_remove

        self._build()
        self.refresh()

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build(self):
        self.configure(padding=12)

        # ── Top row: title + controls ───────────────────────────────
        top = ttk.Frame(self, style="Card.TFrame")
        top.pack(fill="x")

        # Control buttons container (Pack FIRST to secure space on the right)
        btn_frame = ttk.Frame(top, style="Card.TFrame")
        btn_frame.pack(side="right")

        self._title_var = tk.StringVar(value=self.item.title[:70])
        ttk.Label(top, textvariable=self._title_var,
                  style="CardHead.TLabel", anchor="w").pack(side="left", fill="x", expand=True)

        # Open folder (only visible when done)
        self._folder_btn = tk.Button(
            btn_frame, text="📂", command=self._open_folder,
            bg=C["bg_hover"], fg=C["accent_green"],
            relief="flat", font=F["body"], padx=6, pady=2,
            cursor="hand2", activebackground=C["bg_selected"],
        )
        # folder_btn.pack is handled in refresh()

        self._pause_btn = tk.Button(
            btn_frame, text="⏸", command=self._toggle_pause,
            bg=C["bg_hover"], fg=C["accent_yellow"],
            relief="flat", font=F["body"], padx=6, pady=2,
            cursor="hand2", activebackground=C["bg_selected"],
            activeforeground=C["accent_yellow"],
        )
        self._pause_btn.pack(side="left", padx=2)

        # Stop/Cancel button (stops the actual download)
        self._cancel_btn = tk.Button(
            btn_frame, text="⏹", command=self._cancel,
            bg=C["bg_hover"], fg="#EF4444",
            relief="flat", font=("Segoe UI", 12), padx=6, pady=2,
            cursor="hand2", activebackground=C["bg_selected"],
            activeforeground="#EF4444",
        )
        self._cancel_btn.pack(side="left", padx=2)

        # Remove/Clear button (X on the far right)
        tk.Button(
            btn_frame, text="✕", command=self._remove,
            bg=C["bg_hover"], fg=C["text_muted"],
            relief="flat", font=("Segoe UI", 11, "bold"), padx=8, pady=2,
            cursor="hand2", activebackground=C["bg_selected"],
            activeforeground="#EF4444",
        ).pack(side="left", padx=(6, 2))
        # will be shown on completion

        # ── Status badge ────────────────────────────────────────────
        mid = ttk.Frame(self, style="Card.TFrame")
        mid.pack(fill="x", pady=(6, 4))

        self._badge = StatusBadge(mid, status=self.item.status.name)
        self._badge.pack(side="left")

        self._meta_var = tk.StringVar()
        ttk.Label(mid, textvariable=self._meta_var,
                  style="CardMeta.TLabel").pack(side="left", padx=(10, 0))

        # ── Progress bar ────────────────────────────────────────────
        self._progress = AnimatedProgressBar(self)
        self._progress.pack(fill="x", pady=(2, 4))

        # ── Error label (hidden until needed) ──────────────────────
        self._err_var = tk.StringVar()
        self._err_lbl = ttk.Label(self, textvariable=self._err_var,
                                  style="CardError.TLabel", wraplength=440, anchor="w")

        # Divider
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(4, 0))

    # ── Refresh ────────────────────────────────────────────────────────────

    def refresh(self):
        """Update all dynamic widgets from the current item state."""
        item   = self.item
        status = item.status.name
        self._badge.set_status(status)
        self._title_var.set(item.title[:72] + ("…" if len(item.title) > 72 else ""))
        self._progress.set(item.progress)

        # Meta info & button states
        if status == "ACTIVE":
            speed = format_speed(item.speed)
            eta   = format_eta(item.eta)
            self._meta_var.set(f"{speed}  ·  ETA {eta}")
            if self._folder_btn.winfo_ismapped():
                self._folder_btn.pack_forget()
            self._pause_btn.configure(state="normal")
            self._cancel_btn.configure(state="normal")
        elif status == "COMPLETED":
            self._meta_var.set("Done ✓")
            if not self._folder_btn.winfo_ismapped():
                self._folder_btn.pack(side="left", padx=2, before=self._pause_btn)
            self._pause_btn.configure(state="disabled")
            self._cancel_btn.configure(state="disabled")
        elif status == "FAILED":
            self._meta_var.set("Failed")
            if self._folder_btn.winfo_ismapped():
                self._folder_btn.pack_forget()
            self._pause_btn.configure(state="disabled")
            self._cancel_btn.configure(state="disabled")
        elif status == "PAUSED":
            self._meta_var.set("Paused")
            if self._folder_btn.winfo_ismapped():
                self._folder_btn.pack_forget()
            self._pause_btn.configure(state="normal")
            self._cancel_btn.configure(state="normal")
        elif status in ("QUEUED", "FETCHING"):
            self._meta_var.set("Waiting…")
            if self._folder_btn.winfo_ismapped():
                self._folder_btn.pack_forget()
            self._pause_btn.configure(state="normal")
            self._cancel_btn.configure(state="normal")
        elif status == "CANCELLED":
            self._meta_var.set("Cancelled")
            if self._folder_btn.winfo_ismapped():
                self._folder_btn.pack_forget()
            self._pause_btn.configure(state="disabled")
            self._cancel_btn.configure(state="disabled")

        # Pause button label
        if item.is_paused():
            self._pause_btn.configure(text="▶")
        else:
            self._pause_btn.configure(text="⏸")

        # Error message
        if item.error and status in ("FAILED",):
            self._err_var.set(f"⚠  {item.error[:120]}")
            self._err_lbl.pack(fill="x", pady=(2, 0))
        else:
            self._err_lbl.pack_forget()

    # ── Controls ───────────────────────────────────────────────────────────

    def _toggle_pause(self):
        self._on_pause_resume(self.item)
        self.refresh()

    def _cancel(self):
        self._on_cancel(self.item)
        self.refresh()

    def _open_folder(self):
        self._on_open_folder(self.item)

    def _remove(self):
        self._on_remove(self.item)


# ─────────────────────── Queue Panel ────────────────────────────────────────

class DownloadQueuePanel(ttk.Frame):
    """
    The full download-manager panel containing a scrollable list of cards.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="Dark.TFrame", **kwargs)

        self._cards: Dict[str, DownloadCard] = {}   # item id → card
        self._build()

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build(self):
        # Header row
        header = ttk.Frame(self, style="Dark.TFrame")
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(header, text="  DOWNLOAD MANAGER", fg=C["accent"],
                 bg=C["bg_primary"], font=F["subheading"]).pack(side="left")

        self._count_var = tk.StringVar(value="0 items")
        ttk.Label(header, textvariable=self._count_var,
                  style="Muted.TLabel").pack(side="right")

        # Clear All / Clear Completed buttons
        tk.Button(
            header, text="Clear All", command=self.clear_all,
            bg=C["bg_hover"], fg=C["text_secondary"],
            relief="flat", font=F["small"], padx=8, pady=4,
            cursor="hand2", activebackground=C["bg_selected"],
        ).pack(side="right", padx=6)

        tk.Button(
            header, text="Clear Finished", command=self.remove_completed,
            bg=C["bg_hover"], fg=C["text_secondary"],
            relief="flat", font=F["small"], padx=8, pady=4,
            cursor="hand2", activebackground=C["bg_selected"],
        ).pack(side="right", padx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Scrollable card area
        self._scroll = ScrollableFrame(self, bg=C["bg_primary"])
        self._scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # Empty state
        self._empty_lbl = ttk.Label(
            self._scroll.inner,
            text="No downloads yet.\nPaste a URL and click Download.",
            style="Muted.TLabel",
            justify="center",
        )
        self._empty_lbl.pack(expand=True, pady=60)

    # ── Public API ──────────────────────────────────────────────────────────

    def add_item(self, item: DownloadItem) -> DownloadCard:
        """Add a new DownloadCard for *item* and return it."""
        self._empty_lbl.pack_forget()

        card = DownloadCard(
            self._scroll.inner,
            item,
            on_pause_resume=self._toggle_pause,
            on_cancel=self._cancel_item,
            on_open_folder=self._open_folder,
            on_remove=self.remove_item,
        )
        card.pack(fill="x", pady=4, padx=4)
        self._cards[id(item)] = card
        self._update_count()
        return card

    def update_item(self, item: DownloadItem):
        """Refresh the card associated with *item*."""
        card = self._cards.get(id(item))
        if card:
            card.refresh()

    def remove_item(self, item: DownloadItem):
        """Cancel and remove a specific item from the UI."""
        item.cancel()
        card = self._cards.pop(id(item), None)
        if card:
            card.destroy()
        self._update_count()
        if not self._cards:
            self._empty_lbl.pack(expand=True, pady=60)

    def clear_all(self):
        """Cancel and remove all items from the UI."""
        items = [card.item for card in self._cards.values()]
        for item in items:
            self.remove_item(item)

    def remove_completed(self):
        """Remove all completed/cancelled/failed cards."""
        to_remove = [
            (k, c) for k, c in self._cards.items()
            if c.item.status in (
                DownloadStatus.COMPLETED,
                DownloadStatus.CANCELLED,
                DownloadStatus.FAILED,
            )
        ]
        for k, card in to_remove:
            card.destroy()
            del self._cards[k]
        self._update_count()
        if not self._cards:
            self._empty_lbl.pack(expand=True, pady=60)

    # ── Handlers ───────────────────────────────────────────────────────────

    def _toggle_pause(self, item: DownloadItem):
        if item.is_paused():
            item.resume()
        else:
            item.pause()

    def _cancel_item(self, item: DownloadItem):
        item.cancel()

    def _open_folder(self, item: DownloadItem):
        folder = item.output_dir
        if item.filepath and os.path.isfile(item.filepath):
            folder = os.path.dirname(item.filepath)
            subprocess.Popen(f'explorer /select,"{os.path.normpath(item.filepath)}"')
        elif os.path.isdir(folder):
            subprocess.Popen(f'explorer "{os.path.normpath(folder)}"')

    def _update_count(self):
        n = len(self._cards)
        self._count_var.set(f"{n} item{'s' if n != 1 else ''}")
