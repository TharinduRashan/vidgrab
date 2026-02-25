"""
Style Application
=================
Applies TTK theme based on the current COLORS palette.
Call ``apply_theme(root)`` on startup and after every theme switch.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import COLORS as C, FONTS as F


def apply_theme(root: tk.Tk) -> None:
    """Configure all TTK styles using the current COLORS palette."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        style.theme_use("default")

    _configure_frames(style)
    _configure_labels(style)
    _configure_entries(style)
    _configure_buttons(style)
    _configure_treeview(style)
    _configure_scrollbars(style)
    _configure_progressbars(style)
    _configure_notebook(style)
    _configure_combobox(style)
    _configure_checkbutton(style)
    _configure_scale(style)
    _configure_separator(style)
    _configure_spinbox(style)

    root.configure(bg=C["bg_primary"])


# Alias kept for backwards compat with any external code
apply_dark_theme = apply_theme


# ──────────────────────────── Helpers ────────────────────────────────────────

def refresh_treeview_tags(tree: ttk.Treeview):
    """Re-apply alternating-row tag colours on a Treeview after a theme switch."""
    tree.tag_configure("odd",  background=C["bg_tertiary"])
    tree.tag_configure("even", background=C["bg_secondary"])
    tree.tag_configure("best", background=C["bg_hover"])


# ──────────────────────────── Frames ─────────────────────────────────────────

def _configure_frames(s: ttk.Style):
    s.configure("TFrame",       background=C["bg_primary"])
    s.configure("Dark.TFrame",  background=C["bg_primary"])
    s.configure("Card.TFrame",  background=C["bg_secondary"])
    s.configure("Panel.TFrame", background=C["bg_secondary"])


# ──────────────────────────── Labels ─────────────────────────────────────────

def _configure_labels(s: ttk.Style):
    base = dict(background=C["bg_primary"], foreground=C["text_primary"], font=F["body"])
    s.configure("TLabel",           **base)
    s.configure("Dark.TLabel",      **base)
    s.configure("Heading.TLabel",   background=C["bg_primary"],   foreground=C["text_primary"],   font=F["heading"])
    s.configure("Subhead.TLabel",   background=C["bg_primary"],   foreground=C["text_secondary"], font=F["subheading"])
    s.configure("Muted.TLabel",     background=C["bg_primary"],   foreground=C["text_muted"],     font=F["small"])
    s.configure("Accent.TLabel",    background=C["bg_primary"],   foreground=C["accent"],         font=F["body_bold"])
    s.configure("Card.TLabel",      background=C["bg_secondary"],  foreground=C["text_primary"],   font=F["body"])
    s.configure("CardHead.TLabel",  background=C["bg_secondary"],  foreground=C["text_primary"],   font=F["subheading"])
    s.configure("CardMuted.TLabel", background=C["bg_secondary"],  foreground=C["text_muted"],     font=F["small"])
    s.configure("CardMeta.TLabel",  background=C["bg_secondary"],  foreground=C["text_secondary"], font=F["small"])
    s.configure("Success.TLabel",   background=C["bg_primary"],   foreground=C["accent_green"],   font=F["small"])
    s.configure("Error.TLabel",     background=C["bg_primary"],   foreground="#EF4444",            font=F["small"])
    s.configure("CardSuccess.TLabel", background=C["bg_secondary"], foreground=C["accent_green"],  font=F["small"])
    s.configure("CardError.TLabel",   background=C["bg_secondary"], foreground="#EF4444",           font=F["small"])


# ──────────────────────────── Entries ────────────────────────────────────────

def _configure_entries(s: ttk.Style):
    s.configure(
        "TEntry",
        fieldbackground=C["bg_tertiary"],
        foreground=C["text_primary"],
        insertcolor=C["text_primary"],
        bordercolor=C["border"],
        lightcolor=C["border"],
        darkcolor=C["border"],
        relief="flat",
        padding=8,
        font=F["url"],
    )
    s.map(
        "TEntry",
        bordercolor=[("focus", C["border_focus"])],
        lightcolor=[("focus", C["border_focus"])],
        darkcolor=[("focus", C["border_focus"])],
    )


# ──────────────────────────── Buttons ────────────────────────────────────────

def _configure_buttons(s: ttk.Style):
    base = dict(relief="flat", padding=(14, 8), font=F["body_bold"], borderwidth=0)

    # Primary accent (blue)
    s.configure("Accent.TButton",     background=C["accent"],     foreground="#FFFFFF", **base)
    s.map("Accent.TButton",
        background=[("active",  C["accent_dark"]),
                    ("pressed", C["accent_dark"]),
                    ("disabled","#555")],
        foreground=[("disabled", "#888")])

    s.configure("Secondary.TButton",  background=C["bg_hover"],   foreground=C["text_primary"], **base)
    s.map("Secondary.TButton",
        background=[("active", C["bg_selected"]), ("pressed", C["bg_selected"])])

    s.configure("Danger.TButton",     background="#7F1D1D",        foreground="#FECACA", **base)
    s.map("Danger.TButton",
        background=[("active", "#991B1B"), ("pressed", "#7F1D1D")])

    s.configure("Success.TButton",    background="#14532D",        foreground="#BBF7D0", **base)
    s.map("Success.TButton",
        background=[("active", "#166534"), ("pressed", "#14532D")])

    s.configure("Icon.TButton",
        background=C["bg_tertiary"], foreground=C["text_secondary"],
        relief="flat", padding=(6, 4), font=F["small"], borderwidth=0)
    s.map("Icon.TButton",
        background=[("active", C["bg_hover"]), ("pressed", C["bg_selected"])],
        foreground=[("active", C["text_primary"])])


# ──────────────────────────── Treeview ───────────────────────────────────────

def _configure_treeview(s: ttk.Style):
    s.configure(
        "Dark.Treeview",
        background=C["bg_tertiary"],
        foreground=C["text_primary"],
        fieldbackground=C["bg_tertiary"],
        rowheight=30,
        font=F["body"],
        borderwidth=0,
    )
    s.configure(
        "Dark.Treeview.Heading",
        background=C["bg_secondary"],
        foreground=C["text_secondary"],
        font=F["body_bold"],
        relief="flat",
        padding=(8, 6),
    )
    s.map("Dark.Treeview",
        background=[("selected", C["bg_selected"])],
        foreground=[("selected", C["text_primary"])],
    )
    s.map("Dark.Treeview.Heading",
        background=[("active", C["bg_hover"])],
    )


# ──────────────────────────── Scrollbars ─────────────────────────────────────

def _configure_scrollbars(s: ttk.Style):
    s.configure(
        "Dark.Vertical.TScrollbar",
        background=C["scrollbar_bg"],
        troughcolor=C["scrollbar_bg"],
        arrowcolor=C["scrollbar_fg"],
        bordercolor=C["scrollbar_bg"],
        relief="flat", width=8,
    )
    s.map("Dark.Vertical.TScrollbar",
        background=[("active", C["scrollbar_fg"]), ("pressed", C["accent"])])

    s.configure(
        "Dark.Horizontal.TScrollbar",
        background=C["scrollbar_bg"],
        troughcolor=C["scrollbar_bg"],
        arrowcolor=C["scrollbar_fg"],
        bordercolor=C["scrollbar_bg"],
        relief="flat", height=8,
    )


# ──────────────────────────── Progress bars ──────────────────────────────────

def _configure_progressbars(s: ttk.Style):
    s.configure(
        "Blue.Horizontal.TProgressbar",
        background=C["progress_fill"],
        troughcolor=C["progress_bg"],
        bordercolor=C["progress_bg"],
        lightcolor=C["progress_fill"],
        darkcolor=C["progress_fill"],
        thickness=6,
    )
    # Keep "Red.*" alias in case other code references it
    s.configure(
        "Red.Horizontal.TProgressbar",
        background=C["progress_fill"],
        troughcolor=C["progress_bg"],
        bordercolor=C["progress_bg"],
        lightcolor=C["progress_fill"],
        darkcolor=C["progress_fill"],
        thickness=6,
    )
    s.configure(
        "Green.Horizontal.TProgressbar",
        background=C["accent_green"],
        troughcolor=C["progress_bg"],
        bordercolor=C["progress_bg"],
        lightcolor=C["accent_green"],
        darkcolor=C["accent_green"],
        thickness=6,
    )


# ──────────────────────────── Notebook ───────────────────────────────────────

def _configure_notebook(s: ttk.Style):
    s.configure(
        "Dark.TNotebook",
        background=C["bg_primary"],
        bordercolor=C["border"],
        tabmargins=[0, 0, 0, 0],
    )
    s.configure(
        "Dark.TNotebook.Tab",
        background=C["bg_secondary"],
        foreground=C["text_muted"],
        font=F["body_bold"],
        padding=(16, 8),
        borderwidth=0,
    )
    s.map("Dark.TNotebook.Tab",
        background=[("selected", C["bg_primary"]), ("active", C["bg_hover"])],
        foreground=[("selected", C["text_primary"]), ("active", C["text_secondary"])],
    )


# ──────────────────────────── Combobox ───────────────────────────────────────

def _configure_combobox(s: ttk.Style):
    s.configure(
        "TCombobox",
        fieldbackground=C["bg_tertiary"],
        background=C["bg_tertiary"],
        foreground=C["text_primary"],
        arrowcolor=C["text_secondary"],
        bordercolor=C["border"],
        selectbackground=C["bg_selected"],
        selectforeground=C["text_primary"],
        relief="flat",
        padding=8,
    )
    s.map("TCombobox",
        fieldbackground=[("readonly", C["bg_tertiary"])],
        background=[("active", C["bg_hover"])],
    )


# ──────────────────────────── Checkbutton ────────────────────────────────────

def _configure_checkbutton(s: ttk.Style):
    s.configure(
        "TCheckbutton",
        background=C["bg_primary"],
        foreground=C["text_primary"],
        font=F["body"],
        indicatorcolor=C["bg_tertiary"],
        focuscolor="",
    )
    s.map("TCheckbutton",
        indicatorcolor=[("selected", C["accent"])],
        background=[("active", C["bg_primary"])],
    )


# ──────────────────────────── Scale ──────────────────────────────────────────

def _configure_scale(s: ttk.Style):
    s.configure(
        "TScale",
        background=C["bg_primary"],
        troughcolor=C["bg_tertiary"],
        slidercolor=C["accent"],
    )


# ──────────────────────────── Separator ──────────────────────────────────────

def _configure_separator(s: ttk.Style):
    s.configure("TSeparator", background=C["border"])


# ──────────────────────────── Spinbox ────────────────────────────────────────

def _configure_spinbox(s: ttk.Style):
    s.configure(
        "TSpinbox",
        fieldbackground=C["bg_tertiary"],
        foreground=C["text_primary"],
        background=C["bg_tertiary"],
        arrowcolor=C["text_secondary"],
        bordercolor=C["border"],
        relief="flat",
        padding=6,
    )
