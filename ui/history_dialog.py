"""
History Dialog
==============
Shows the download history stored in %APPDATA%/YTDownloader/history.json.
"""

import tkinter as tk
from tkinter import ttk

from ui.theme import COLORS as C, FONTS as F
from utils.settings import settings


class HistoryDialog(tk.Toplevel):
    """Modal dialog showing download history."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Download History")
        self.geometry("860x480")
        self.resizable(True, True)
        self.configure(bg=C["bg_primary"])
        self.grab_set()
        self.transient(parent)
        self._build()
        self._load()

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build(self):
        header = ttk.Frame(self, style="Dark.TFrame", padding=(16, 12))
        header.pack(fill="x")
        tk.Label(header, text="🕐  Download History", fg=C["text_primary"],
                 bg=C["bg_primary"], font=F["heading"]).pack(side="left")

        tk.Button(
            header, text="Clear History",
            bg=C["bg_hover"], fg=C["accent"],
            font=F["small"], relief="flat", padx=10, pady=4,
            cursor="hand2", command=self._clear,
        ).pack(side="right")

        ttk.Separator(self).pack(fill="x")

        cols = ("Date", "Title", "Format", "Path")
        tree_frame = ttk.Frame(self, style="Dark.TFrame", padding=8)
        tree_frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Dark.Treeview", selectmode="browse",
        )
        for col, width in zip(cols, [130, 360, 80, 270]):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=width, anchor="w", minwidth=60)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._tree.yview,
                             style="Dark.Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

        # Tag for alternating rows
        self._tree.tag_configure("odd",  background=C["bg_tertiary"])
        self._tree.tag_configure("even", background=C["bg_secondary"])

        # Double-click → open folder
        self._tree.bind("<Double-1>", self._open_path)

        brow = ttk.Frame(self, style="Dark.TFrame", padding=(16, 8))
        brow.pack(fill="x")
        ttk.Label(brow, text="Double-click a row to open its folder.",
                  style="Muted.TLabel").pack(side="left")
        tk.Button(brow, text="Close", bg=C["bg_hover"], fg=C["text_primary"],
                  font=F["small"], relief="flat", padx=12, pady=5,
                  command=self.destroy, cursor="hand2").pack(side="right")

    def _load(self):
        history = settings.load_history()
        self._tree.delete(*self._tree.get_children())
        for i, entry in enumerate(history):
            tag = "odd" if i % 2 else "even"
            audio = " (Audio)" if entry.get("audio") else ""
            self._tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                entry.get("date", ""),
                entry.get("title", ""),
                entry.get("format", "") + audio,
                entry.get("path", ""),
            ))

    def _clear(self):
        import os, json
        hf = settings.history_file
        if os.path.isfile(hf):
            try:
                with open(hf, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except OSError:
                pass
        self._load()

    def _open_path(self, _):
        sel = self._tree.selection()
        if not sel:
            return
        import os, subprocess
        path = self._tree.item(sel[0], "values")[3]
        if not path:
            return
        path = os.path.normpath(path)
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        if os.path.isfile(path):
            subprocess.Popen(f'explorer /select,"{path}"')
        elif os.path.isdir(folder):
            subprocess.Popen(f'explorer "{folder}"')
