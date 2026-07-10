from __future__ import annotations

from enum import Enum


class StatusKind(str, Enum):
    NEUTRAL = "neutral"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class PopupPosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


class NavigationPosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"


def enum_value(value, enum_type, default):
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value).lower())
    except (TypeError, ValueError):
        return default


__all__ = ["NavigationPosition", "PopupPosition", "StatusKind"]
