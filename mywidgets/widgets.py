"""Stable compatibility facade for mywidgets widget classes.

Concrete implementations live in focused modules. Existing imports from
``mywidgets.widgets`` and ``mywidgets.controls`` remain supported.
"""

from __future__ import annotations

from . import buttons as _buttons
from . import data as _data
from . import display as _display
from . import feedback as _feedback
from . import inputs as _inputs
from . import typography as _typography
from .buttons import *
from .data import *
from .display import *
from .feedback import *
from .inputs import *
from .typography import *
from .theme import ThemeManager, ThemeMode, apply_theme


def set_theme(mode: ThemeMode, accent: str | None = None):
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    manager = ThemeManager.instance()
    apply_theme(app, mode, accent or manager.accent)


__all__ = [
    *_typography.__all__,
    *_buttons.__all__,
    *_inputs.__all__,
    *_display.__all__,
    *_data.__all__,
    *_feedback.__all__,
    "set_theme",
]
