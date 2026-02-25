"""
Reusable UI Widgets
===================
Custom Tkinter / ttk widgets used throughout the application.
All colours are sourced from the mutable COLORS dict so they stay
correct after a theme switch (for newly-created instances).
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from ui.theme import COLORS as C, FONTS as F, STATUS_COLORS


# ──────────────────────────── Rounded Canvas Button ─────────────────────────

class RoundedButton(tk.Canvas):
    """A visually styled button drawn on a Canvas (supports radius)."""

    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable] = None,
        bg: str = None,
        fg: str = "#FFFFFF",
        hover_bg: str = None,
        font=F["body_bold"],
        radius: int = 8,
        padx: int = 18,
        pady: int = 9,
        **kwargs,
    ):
        bg       = bg       or C["accent"]
        hover_bg = hover_bg or C["accent_dark"]

        self._bg       = bg
        self._hover_bg = hover_bg
        self._fg       = fg
        self._text     = text
        self._font     = font
        self._radius   = radius
        self._command  = command

        tmp = tk.Label(parent, text=text, font=font)
        tw  = tmp.winfo_reqwidth()
        th  = tmp.winfo_reqheight()
        tmp.destroy()

        w = tw + padx * 2
        h = th + pady * 2

        super().__init__(parent, width=w, height=h,
                         bg=parent.cget("bg"), highlightthickness=0, **kwargs)
        self._w = w
        self._h = h
        self._draw(bg)

        self.bind("<Enter>",          lambda _: self._draw(hover_bg))
        self.bind("<Leave>",          lambda _: self._draw(bg))
        self.bind("<ButtonPress-1>",  lambda _: self._draw(hover_bg))
        self.bind("<ButtonRelease-1>", self._on_click)

    def _draw(self, color: str):
        self.delete("all")
        r = self._radius
        w, h = self._w, self._h
        self.create_polygon(
            r, 0, w - r, 0,
            w, r, w, h - r,
            w - r, h, r, h,
            0, h - r, 0, r,
            smooth=True, fill=color, outline="",
        )
        self.create_text(w // 2, h // 2, text=self._text,
                         fill=self._fg, font=self._font, anchor="center")

    def _on_click(self, _):
        self._draw(self._bg)
        if self._command:
            self._command()

    def configure_text(self, text: str):
        self._text = text
        self._draw(self._bg)


# ──────────────────────────── Animated Progress Bar ──────────────────────────

class AnimatedProgressBar(ttk.Frame):
    """
    Horizontal progress bar with percentage label.
    Turns green when value reaches 100.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self._value = tk.DoubleVar(value=0.0)

        self._bar = ttk.Progressbar(
            self, variable=self._value,
            maximum=100, mode="determinate",
            style="Blue.Horizontal.TProgressbar",
        )
        self._bar.pack(fill="x", side="left", expand=True)

        self._label = ttk.Label(self, text="0%",
                                style="CardMuted.TLabel", width=5, anchor="e")
        self._label.pack(side="left", padx=(6, 0))

    def set(self, value: float):
        v = max(0.0, min(100.0, value))
        self._value.set(v)
        self._label.configure(text=f"{v:.0f}%")
        style = "Green.Horizontal.TProgressbar" if v >= 100 else "Blue.Horizontal.TProgressbar"
        self._bar.configure(style=style)


# ──────────────────────────── Status Badge ─────────────────────────────────

class StatusBadge(tk.Label):
    """Coloured pill label showing a download status."""

    def __init__(self, parent, status: str = "QUEUED", **kwargs):
        # Prevent 'multiple values for keyword argument' error
        kwargs.pop("bg", None)
        kwargs.pop("background", None)
        kwargs.pop("fg", None)
        kwargs.pop("foreground", None)

        bg, fg = STATUS_COLORS.get(status, ("#555", "#fff"))
        super().__init__(
            parent, text=f" {status} ",
            bg=bg, fg=fg,
            font=F["small"], padx=4, pady=2,
            relief="flat",
            **kwargs,
        )

    def set_status(self, status: str):
        bg, fg = STATUS_COLORS.get(status, ("#555", "#fff"))
        self.configure(text=f" {status} ", bg=bg, fg=fg)


# ──────────────────────────── Scrollable Frame ───────────────────────────────

class ScrollableFrame(ttk.Frame):
    """A frame inside a Canvas with a vertical scrollbar."""

    def __init__(self, parent, bg: str = None, **kwargs):
        bg = bg or C["bg_primary"]
        super().__init__(parent, **kwargs)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        vscroll      = ttk.Scrollbar(self, orient="vertical",
                                     command=self._canvas.yview,
                                     style="Dark.Vertical.TScrollbar")
        self._canvas.configure(yscrollcommand=vscroll.set)

        vscroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.inner   = ttk.Frame(self._canvas, style="Dark.TFrame")
        self._window = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>",    self._on_inner_configure)
        self._canvas.bind("<Configure>",  self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.inner.bind("<MouseWheel>",   self._on_mousewheel)

    def _on_inner_configure(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ──────────────────────────── Tooltip ────────────────────────────────────────

class Tooltip:
    """Simple hover tooltip for any widget."""

    def __init__(self, widget: tk.Widget, text: str):
        self._widget  = widget
        self._text    = text
        self._tip_win = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _):
        if self._tip_win:
            return
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip_win = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self._text,
            bg=C["bg_hover"], fg=C["text_primary"],
            font=F["small"], relief="flat", padx=8, pady=4,
        ).pack()

    def _hide(self, _):
        if self._tip_win:
            self._tip_win.destroy()
            self._tip_win = None


# ──────────────────────────── Section Header ─────────────────────────────────

class SectionHeader(ttk.Frame):
    """A labelled section divider with an accent dot."""

    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, style="Dark.TFrame", **kwargs)

        tk.Label(self, text="●", fg=C["accent"],
                 bg=C["bg_primary"], font=F["small"]).pack(side="left")
        ttk.Label(self, text=f"  {title}", style="Heading.TLabel").pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(
            side="left", fill="x", expand=True, padx=(12, 0), pady=6
        )
