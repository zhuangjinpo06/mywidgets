from __future__ import annotations

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QLabel


class _TextLabel(QLabel):
    def __init__(self, text: str = "", role: str = "body", parent=None):
        super().__init__(text, parent)
        self.setProperty("role", role)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)


class CaptionText(_TextLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, "caption", parent)


class BodyText(_TextLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, "body", parent)


class StrongText(_TextLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, "strong", parent)


class SubtitleText(_TextLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, "subtitle", parent)


class TitleText(_TextLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, "pageTitle", parent)


class LargeTitleText(_TextLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, "largeTitle", parent)


class DisplayText(_TextLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, "display", parent)


class HyperlinkText(_TextLabel):
    activated = Signal(str)

    def __init__(self, text: str = "", url: str = "", parent=None):
        super().__init__(text, "hyperlink", parent)
        self.url = url
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setAccessibleName(text)

    def activate(self):
        if not self.url:
            return False
        self.activated.emit(self.url)
        QDesktopServices.openUrl(QUrl(self.url))
        return True

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.activate()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space) and self.activate():
            event.accept()
            return
        super().keyPressEvent(event)


__all__ = [
    "BodyText",
    "CaptionText",
    "DisplayText",
    "HyperlinkText",
    "LargeTitleText",
    "StrongText",
    "SubtitleText",
    "TitleText",
]
