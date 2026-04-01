"""
app/utils.py — Shared helpers and constants used across all screens and widgets.
"""
import logging

from kivy.app import App
from kivy.metrics import sp

from database import DatabaseManager

logger = logging.getLogger(__name__)

# ── Day-of-week colour palette ───────────────────────────────────────────────
DAY_COLORS = {
    0: (0.3, 0.7, 0.3, 1),   # Monday    – Green
    1: (0.1, 0.5, 0.8, 1),   # Tuesday   – Blue
    2: (0.6, 0.3, 0.8, 1),   # Wednesday – Purple
    3: (1.0, 0.6, 0.2, 1),   # Thursday  – Orange
    4: (0.0, 0.6, 0.6, 1),   # Friday    – Teal
    5: (0.9, 0.8, 0.2, 1),   # Saturday  – Yellow
    6: (0.8, 0.3, 0.3, 1),   # Sunday    – Red
}


def get_database() -> DatabaseManager:
    """Return the shared DatabaseManager from the running app."""
    return App.get_running_app().database


def get_sp(size_name: str) -> int:
    """Return a scaled-pixel size for the given size name."""
    sizes = {
        "header": sp(24),
        "title": sp(20),
        "body": sp(16),
        "button": sp(14),
    }
    return sizes.get(size_name, sp(16))


def is_mobile() -> bool:
    """Return True when running on a mobile device."""
    from kivy.metrics import Metrics
    return Metrics.platform in ("android", "ios") or Metrics.dpi < 200
