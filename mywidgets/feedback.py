from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .core import install_window_icon
from .display import IndeterminateProgressRing, StatusBadge
from .enums import PopupPosition, StatusKind, enum_value
from .typography import CaptionText, StrongText


class Toast(QFrame):
    closed = Signal()

    def __init__(
        self,
        title: str,
        content: str,
        kind: StatusKind | str = StatusKind.INFO,
        parent=None,
    ):
        super().__init__(parent)
        self.kind = enum_value(kind, StatusKind, StatusKind.INFO)
        self.setObjectName("Toast")
        install_window_icon(self, "toast")
        self.setProperty("kind", self.kind.value)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(280)
        self.setMaximumWidth(420)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(StatusBadge(self.kind.value[:1].upper(), self.kind))
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        text_layout.addWidget(StrongText(title))
        label = CaptionText(content)
        label.setWordWrap(True)
        text_layout.addWidget(label)
        layout.addLayout(text_layout, 1)

    def closeEvent(self, event):
        ToastManager._remove(self)
        self.closed.emit()
        super().closeEvent(event)


class _ToastHostFilter(QObject):
    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.Show, QEvent.Move):
            ToastManager._position(watched)
        if event.type() == QEvent.Destroy:
            ToastManager._drop_host(watched)
        return False


class ToastManager:
    _active: dict[QWidget, list[tuple[Toast, PopupPosition]]] = defaultdict(list)
    _filters: dict[QWidget, _ToastHostFilter] = {}

    @classmethod
    def show(
        cls,
        parent: QWidget,
        title: str,
        content: str,
        kind: StatusKind | str = StatusKind.INFO,
        duration: int = 1800,
        position: PopupPosition | str = PopupPosition.TOP_RIGHT,
    ):
        if parent is None:
            raise ValueError("Toast requires a parent widget")
        popup_position = enum_value(position, PopupPosition, PopupPosition.TOP_RIGHT)
        toast = Toast(title, content, kind, parent)
        if parent not in cls._filters:
            event_filter = _ToastHostFilter(parent)
            parent.installEventFilter(event_filter)
            cls._filters[parent] = event_filter
        cls._active[parent].append((toast, popup_position))
        toast.adjustSize()
        toast.show()
        toast.raise_()
        cls._position(parent)
        if duration > 0:
            QTimer.singleShot(duration, toast.close)
        return toast

    @classmethod
    def info(cls, parent, title, content, duration=1800, position=PopupPosition.TOP_RIGHT):
        return cls.show(parent, title, content, StatusKind.INFO, duration, position)

    @classmethod
    def success(cls, parent, title, content, duration=1800, position=PopupPosition.TOP_RIGHT):
        return cls.show(parent, title, content, StatusKind.SUCCESS, duration, position)

    @classmethod
    def warning(cls, parent, title, content, duration=1800, position=PopupPosition.TOP_RIGHT):
        return cls.show(parent, title, content, StatusKind.WARNING, duration, position)

    @classmethod
    def error(cls, parent, title, content, duration=1800, position=PopupPosition.TOP_RIGHT):
        return cls.show(parent, title, content, StatusKind.ERROR, duration, position)

    @classmethod
    def close_all(cls, parent: QWidget | None = None):
        hosts = [parent] if parent is not None else list(cls._active)
        for host in hosts:
            for toast, _ in list(cls._active.get(host, [])):
                toast.close()

    @classmethod
    def _remove(cls, toast: Toast):
        parent = toast.parentWidget()
        if parent not in cls._active:
            return
        cls._active[parent] = [item for item in cls._active[parent] if item[0] is not toast]
        if not cls._active[parent]:
            cls._active.pop(parent, None)
            event_filter = cls._filters.pop(parent, None)
            if event_filter is not None:
                parent.removeEventFilter(event_filter)
        else:
            QTimer.singleShot(0, lambda p=parent: cls._position(p))

    @classmethod
    def _drop_host(cls, parent):
        cls._active.pop(parent, None)
        cls._filters.pop(parent, None)

    @classmethod
    def _position(cls, parent: QWidget):
        entries = [(toast, pos) for toast, pos in cls._active.get(parent, []) if toast.isVisible()]
        if not entries:
            return
        margin = 20
        grouped: dict[PopupPosition, list[Toast]] = defaultdict(list)
        for toast, position in entries:
            grouped[position].append(toast)
        for position, toasts in grouped.items():
            if position in (PopupPosition.BOTTOM, PopupPosition.BOTTOM_LEFT, PopupPosition.BOTTOM_RIGHT):
                y = parent.height() - margin
                iterable = reversed(toasts)
                for toast in iterable:
                    toast.adjustSize()
                    y -= toast.height()
                    toast.move(cls._x_for(parent, toast, position, margin), max(margin, y))
                    y -= 10
            else:
                y = margin
                for toast in toasts:
                    toast.adjustSize()
                    toast.move(cls._x_for(parent, toast, position, margin), y)
                    y += toast.height() + 10

    @staticmethod
    def _x_for(parent, toast, position, margin):
        if position in (PopupPosition.TOP_LEFT, PopupPosition.BOTTOM_LEFT, PopupPosition.LEFT):
            return margin
        if position in (PopupPosition.TOP, PopupPosition.BOTTOM, PopupPosition.CENTER):
            return max(margin, (parent.width() - toast.width()) // 2)
        return max(margin, parent.width() - toast.width() - margin)


class StateTooltip(QFrame):
    closed = Signal()

    def __init__(self, title: str, content: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("StateTooltip")
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        install_window_icon(self, "toast")
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        self.progress = IndeterminateProgressRing()
        self.progress.setFixedSize(26, 26)
        layout.addWidget(self.progress)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_label = StrongText(title)
        self.content_label = CaptionText(content)
        self.content_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.content_label)
        layout.addLayout(text_layout, 1)

    def set_state(self, success: bool, content: str = "", duration: int = 1200):
        self.progress.hide()
        self.setProperty("kind", "success" if success else "error")
        self.content_label.setText(content)
        self.style().unpolish(self)
        self.style().polish(self)
        if duration > 0:
            QTimer.singleShot(duration, self.close)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


__all__ = ["StateTooltip", "Toast", "ToastManager"]
