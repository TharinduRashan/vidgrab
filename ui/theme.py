"""
Theme Configuration
===================
Dual-mode dark / light colour system with a blue accent.

``COLORS`` is a **mutable** dict used application-wide.
On theme switch it is updated *in-place* so every module that
imported ``from ui.theme import COLORS as C`` automatically sees
the new values for future widget construction.

For existing widgets that have already been painted, call
``theme_manager.retheme_all(root)`` which walks the full widget tree.
"""

from typing import Callable, Dict, List, Tuple

# ──────────────────────────── Palettes ──────────────────────────────────────

_DARK: Dict[str, str] = {
    # Backgrounds
    "bg_primary":    "#0B1628",   # deep navy
    "bg_secondary":  "#112040",   # card / panel
    "bg_tertiary":   "#172B52",   # input fields, table rows
    "bg_hover":      "#1D3461",   # hover
    "bg_selected":   "#1E3A72",   # selected row

    # Accents (blue)
    "accent":        "#2563EB",   # primary blue
    "accent_dark":   "#1D4ED8",   # pressed / darker blue
    "accent_blue":   "#3B82F6",   # lighter blue info
    "accent_green":  "#22C55E",
    "accent_yellow": "#F59E0B",
    "accent_purple": "#8B5CF6",

    # Text
    "text_primary":  "#EBF2FF",
    "text_secondary":"#7B96C2",
    "text_muted":    "#3D5A87",

    # Borders
    "border":        "#1A3260",
    "border_focus":  "#2563EB",

    # Progress bars
    "progress_bg":   "#172B52",
    "progress_fill": "#2563EB",
    "progress_done": "#22C55E",

    # Scrollbar
    "scrollbar_bg":  "#172B52",
    "scrollbar_fg":  "#2A4A8A",

    # Misc
    "mode": "dark",
}

_LIGHT: Dict[str, str] = {
    # Backgrounds
    "bg_primary":    "#F0F5FF",   # pale blue-white
    "bg_secondary":  "#FFFFFF",
    "bg_tertiary":   "#E5EDFF",
    "bg_hover":      "#D6E4FF",
    "bg_selected":   "#BFCFFF",

    # Accents (same blue for consistency)
    "accent":        "#2563EB",
    "accent_dark":   "#1D4ED8",
    "accent_blue":   "#3B82F6",
    "accent_green":  "#16A34A",
    "accent_yellow": "#D97706",
    "accent_purple": "#7C3AED",

    # Text
    "text_primary":  "#0D1B40",
    "text_secondary":"#374D6B",
    "text_muted":    "#7A8EA8",

    # Borders
    "border":        "#C2D3EF",
    "border_focus":  "#2563EB",

    # Progress bars
    "progress_bg":   "#DBEAFE",
    "progress_fill": "#2563EB",
    "progress_done": "#16A34A",

    # Scrollbar
    "scrollbar_bg":  "#E5EDFF",
    "scrollbar_fg":  "#BFCFFF",

    # Misc
    "mode": "light",
}

# ──────────────────────────── Mutable global dict ───────────────────────────

# Start in dark mode.  Updated *in-place* on every theme switch so that
# all `from ui.theme import COLORS as C` references stay live.
COLORS: Dict[str, str] = dict(_DARK)

# ──────────────────────────── Fonts ────────────────────────────────────────

FONTS = {
    "title":      ("Segoe UI", 22, "bold"),
    "heading":    ("Segoe UI", 13, "bold"),
    "subheading": ("Segoe UI", 11, "bold"),
    "body":       ("Segoe UI", 10),
    "body_bold":  ("Segoe UI", 10, "bold"),
    "small":      ("Segoe UI", 9),
    "mono":       ("Consolas", 9),
    "url":        ("Segoe UI", 11),
}

# ──────────────────────────── Dimensions ────────────────────────────────────

DIMENSIONS = {
    "window_width":    1400,
    "window_height":   880,
    "min_width":       1100,
    "min_height":      680,
    "padding":         12,
    "padding_large":   20,
    "corner_radius":   8,
    "button_height":   36,
    "input_height":    40,
    "thumbnail_width": 200,
    "thumbnail_height":112,
    "progress_height": 6,
}

# ──────────────────────────── Status badge colours ───────────────────────────

STATUS_COLORS = {
    "QUEUED":    ("#6366F1", "#fff"),
    "FETCHING":  ("#F59E0B", "#000"),
    "ACTIVE":    ("#2563EB", "#fff"),
    "PAUSED":    ("#F59E0B", "#000"),
    "COMPLETED": ("#22C55E", "#000"),
    "FAILED":    ("#EF4444", "#fff"),
    "CANCELLED": ("#6B7280", "#fff"),
}

# ──────────────────────────── Theme Manager ──────────────────────────────────

class _ThemeManager:
    """
    Manages the active dark / light palette.

    Usage
    -----
    from ui.theme import theme_manager
    theme_manager.toggle(root)   # switches and repaints all widgets
    """

    def __init__(self):
        self._mode: str = "dark"
        self._callbacks: List[Callable] = []

    # ── Introspection ──────────────────────────────────────────────────────

    @property
    def is_dark(self) -> bool:
        return self._mode == "dark"

    @property
    def mode(self) -> str:
        return self._mode

    # ── Switching ──────────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> Tuple[Dict, Dict]:
        """
        Switch to *mode* ('dark' or 'light').
        Returns (old_colors_snapshot, new_colors_snapshot) for the walker.
        """
        if mode == self._mode:
            return dict(COLORS), dict(COLORS)

        old_snapshot = dict(COLORS)
        palette = _DARK if mode == "dark" else _LIGHT
        COLORS.update(palette)          # mutate in-place → all `C` refs see it
        self._mode = mode
        return old_snapshot, dict(COLORS)

    def toggle(self) -> Tuple[Dict, Dict]:
        """Flip between dark and light. Returns (old, new) colour snapshots."""
        target = "light" if self._mode == "dark" else "dark"
        return self.set_mode(target)

    # ── Widget re-theming ──────────────────────────────────────────────────

    @staticmethod
    def retheme_all(root, old_colors: Dict, new_colors: Dict):
        """
        Walk the entire widget tree and replace any colour that belongs to
        the *old* palette with its equivalent in the *new* palette.
        """
        # Build {old_hex_lower: new_hex} swap map (skip values that didn't change)
        swap: Dict[str, str] = {}
        for role, old_val in old_colors.items():
            if role == "mode":
                continue
            new_val = new_colors.get(role, old_val)
            if old_val.lower() != new_val.lower():
                swap[old_val.lower()] = new_val

        if not swap:
            return

        _retheme_widget(root, swap)

    # ── Callback registration (for modules that need to react) ────────────

    def register(self, cb: Callable):
        """Register a zero-arg callback to be fired after every theme switch."""
        self._callbacks.append(cb)

    def fire_callbacks(self):
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                pass


def _retheme_widget(widget, swap: Dict[str, str]):
    """Recursively walk *widget* and its children, swapping palette colours."""
    import tkinter as tk

    ATTRS = [
        ("bg",         "bg"),
        ("background", "background"),
        ("fg",         "fg"),
        ("foreground", "foreground"),
        ("insertbackground", "insertbackground"),
        ("highlightcolor",   "highlightcolor"),
        ("highlightbackground", "highlightbackground"),
        ("activebackground", "activebackground"),
        ("activeforeground", "activeforeground"),
        ("selectbackground", "selectbackground"),
        ("selectforeground", "selectforeground"),
    ]

    for getter, setter in ATTRS:
        try:
            val = widget.cget(getter)
            if val and isinstance(val, str) and val.lower() in swap:
                widget.configure(**{setter: swap[val.lower()]})
        except Exception:
            pass

    # Canvas: update its own bg
    if isinstance(widget, tk.Canvas):
        try:
            val = widget.cget("bg")
            if val and val.lower() in swap:
                widget.configure(bg=swap[val.lower()])
        except Exception:
            pass

    for child in widget.winfo_children():
        _retheme_widget(child, swap)


# Singleton
theme_manager = _ThemeManager()
