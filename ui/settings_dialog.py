"""
Settings Dialog
===============
Modal settings window for configuring download folder, concurrency,
audio format, proxies, etc.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ui.theme import COLORS as C, FONTS as F
from utils.settings import settings


class SettingsDialog(tk.Toplevel):
    """Modal settings window."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("540x520")
        self.resizable(False, False)
        self.configure(bg=C["bg_primary"])
        self.grab_set()
        self.transient(parent)

        self._vars: dict = {}
        self._build()
        self._load_current()

        # Centre over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build(self):
        # Title bar
        tk.Label(self, text="⚙  Settings", fg=C["text_primary"],
                 bg=C["bg_primary"], font=F["heading"]).pack(pady=(16, 8), padx=20, anchor="w")

        ttk.Separator(self).pack(fill="x")

        body = ttk.Frame(self, style="Dark.TFrame", padding=20)
        body.pack(fill="both", expand=True)

        # ── Download folder ────────────────────────────────────────
        self._section(body, "Downloads")
        frow = ttk.Frame(body, style="Dark.TFrame")
        frow.pack(fill="x", pady=(0, 12))

        self._vars["download_folder"] = tk.StringVar()
        ttk.Entry(frow, textvariable=self._vars["download_folder"],
                  width=38).pack(side="left", fill="x", expand=True)
        tk.Button(
            frow, text="Browse…",
            bg=C["bg_hover"], fg=C["text_primary"],
            font=F["small"], relief="flat", padx=8, pady=5,
            cursor="hand2", command=self._browse_folder,
        ).pack(side="left", padx=(6, 0))

        # Concurrent downloads
        crow = ttk.Frame(body, style="Dark.TFrame")
        crow.pack(fill="x", pady=(0, 4))
        ttk.Label(crow, text="Concurrent downloads:", style="Dark.TLabel").pack(side="left")
        self._vars["concurrent_downloads"] = tk.IntVar()
        ttk.Spinbox(
            crow, textvariable=self._vars["concurrent_downloads"],
            from_=1, to=8, width=4,
        ).pack(side="left", padx=(8, 0))

        # ── Audio ──────────────────────────────────────────────────
        self._section(body, "Audio")
        arow = ttk.Frame(body, style="Dark.TFrame")
        arow.pack(fill="x", pady=(0, 4))
        ttk.Label(arow, text="Format:", style="Dark.TLabel", width=14).pack(side="left")
        self._vars["audio_format"] = tk.StringVar()
        ttk.Combobox(
            arow, textvariable=self._vars["audio_format"],
            values=["mp3", "m4a", "wav", "opus", "aac"],
            state="readonly", width=10,
        ).pack(side="left")

        qrow = ttk.Frame(body, style="Dark.TFrame")
        qrow.pack(fill="x", pady=(0, 4))
        ttk.Label(qrow, text="Quality (kbps):", style="Dark.TLabel", width=14).pack(side="left")
        self._vars["audio_quality"] = tk.StringVar()
        ttk.Combobox(
            qrow, textvariable=self._vars["audio_quality"],
            values=["128", "160", "192", "256", "320"],
            state="readonly", width=10,
        ).pack(side="left")

        # ── Behaviour ─────────────────────────────────────────────
        self._section(body, "Behaviour")
        for key, label in [
            ("open_folder_when_done", "Open folder when download completes"),
            ("save_history",          "Save download history"),
            ("auto_retry",            "Automatically retry failed downloads"),
            ("download_thumbnail",    "Also download video thumbnail"),
        ]:
            self._vars[key] = tk.BooleanVar()
            ttk.Checkbutton(
                body, text=label,
                variable=self._vars[key],
                style="TCheckbutton",
            ).pack(anchor="w", pady=1)

        rrow = ttk.Frame(body, style="Dark.TFrame")
        rrow.pack(fill="x", pady=(4, 0))
        ttk.Label(rrow, text="Retry attempts:", style="Dark.TLabel", width=14).pack(side="left")
        self._vars["retry_count"] = tk.IntVar()
        ttk.Spinbox(rrow, textvariable=self._vars["retry_count"],
                    from_=1, to=10, width=4).pack(side="left", padx=(8, 0))

        # ── Network ────────────────────────────────────────────────
        self._section(body, "Network (optional)")
        nrow = ttk.Frame(body, style="Dark.TFrame")
        nrow.pack(fill="x", pady=(0, 4))
        ttk.Label(nrow, text="Proxy:", style="Dark.TLabel", width=14).pack(side="left")
        self._vars["proxy"] = tk.StringVar()
        ttk.Entry(nrow, textvariable=self._vars["proxy"], width=28).pack(side="left")

        lrow = ttk.Frame(body, style="Dark.TFrame")
        lrow.pack(fill="x")
        ttk.Label(lrow, text="Rate limit:", style="Dark.TLabel", width=14).pack(side="left")
        self._vars["rate_limit"] = tk.StringVar()
        ttk.Entry(lrow, textvariable=self._vars["rate_limit"], width=12).pack(side="left")
        ttk.Label(lrow, text="  e.g. 2M, 500K", style="Muted.TLabel").pack(side="left")

        # ── Buttons ────────────────────────────────────────────────
        ttk.Separator(self).pack(fill="x")
        brow = ttk.Frame(self, style="Dark.TFrame", padding=(20, 12))
        brow.pack(fill="x")

        tk.Button(
            brow, text="Reset to Defaults",
            bg=C["bg_hover"], fg=C["text_secondary"],
            font=F["small"], relief="flat", padx=10, pady=6,
            command=self._reset, cursor="hand2",
        ).pack(side="left")

        tk.Button(
            brow, text="Cancel",
            bg=C["bg_hover"], fg=C["text_primary"],
            font=F["small"], relief="flat", padx=10, pady=6,
            command=self.destroy, cursor="hand2",
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            brow, text="Save Settings",
            bg=C["accent"], fg="#FFFFFF",
            font=F["body_bold"], relief="flat", padx=16, pady=6,
            command=self._save, cursor="hand2",
        ).pack(side="right")

    def _section(self, parent, title: str):
        ttk.Label(parent, text=title.upper(),
                  style="Subhead.TLabel").pack(anchor="w", pady=(12, 4))

    # ── Load / Save ────────────────────────────────────────────────────────

    def _load_current(self):
        for key, var in self._vars.items():
            val = settings.get(key)
            if val is not None:
                try:
                    var.set(val)
                except Exception:
                    pass

    def _save(self):
        data = {}
        for key, var in self._vars.items():
            data[key] = var.get()
        settings.update(data)
        messagebox.showinfo("Settings", "Settings saved successfully!", parent=self)
        self.destroy()

    def _reset(self):
        if messagebox.askyesno("Reset", "Reset all settings to defaults?", parent=self):
            settings.reset()
            self._load_current()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Download Folder", parent=self)
        if folder:
            self._vars["download_folder"].set(folder)
