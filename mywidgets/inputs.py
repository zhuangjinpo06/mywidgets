from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QPlainTextEdit,
    QSlider,
    QSpinBox,
    QTextEdit,
)

from .core import IconResolver
from .control_style import install_arrow_overlay
from .theme import ThemeManager


class TextInput(QLineEdit):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("TextInput")
        self.setClearButtonEnabled(True)


class PasswordInput(TextInput):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setEchoMode(QLineEdit.Password)
        self._lock_action = self.addAction(
            IconResolver.resolve("lock", "muted"), QLineEdit.LeadingPosition
        )
        self._reveal_action = self.addAction(
            IconResolver.resolve("eye", "muted"), QLineEdit.TrailingPosition
        )
        self._reveal_action.triggered.connect(self._toggle_password)
        self._refresh_actions()
        ThemeManager.instance().themeChanged.connect(self._refresh_actions)

    def _refresh_actions(self, palette=None):
        self._lock_action.setIcon(IconResolver.resolve("lock", "muted"))
        icon_name = "eye_off" if self.echoMode() == QLineEdit.Normal else "eye"
        self._reveal_action.setIcon(IconResolver.resolve(icon_name, "muted"))
        self._reveal_action.setToolTip(
            "隐藏密码" if self.echoMode() == QLineEdit.Normal else "显示密码"
        )

    def _toggle_password(self):
        self.setEchoMode(
            QLineEdit.Password if self.echoMode() == QLineEdit.Normal else QLineEdit.Normal
        )
        self._refresh_actions()


class NumberInput(QSpinBox):
    def __init__(self, value: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("NumberInput")
        install_arrow_overlay(self, "spin")
        self.setValue(value)


class DoubleNumberInput(QDoubleSpinBox):
    def __init__(self, value: float = 0.0, parent=None):
        super().__init__(parent)
        self.setObjectName("DoubleNumberInput")
        install_arrow_overlay(self, "spin")
        self.setDecimals(2)
        self.setValue(value)


class SearchInput(QLineEdit):
    searchRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchInput")
        self.setClearButtonEnabled(True)
        self.setPlaceholderText("搜索")
        self._search_action = self.addAction(
            IconResolver.resolve("search", "muted"), QLineEdit.LeadingPosition
        )
        self._search_action.setToolTip("搜索")
        self._search_action.triggered.connect(
            lambda checked=False: self.searchRequested.emit(self.text())
        )
        self._refresh_icon()
        self.returnPressed.connect(lambda: self.searchRequested.emit(self.text()))
        ThemeManager.instance().themeChanged.connect(self._refresh_icon)

    def _refresh_icon(self, palette=None):
        self._search_action.setIcon(IconResolver.resolve("search", "muted"))


class TextArea(QTextEdit):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("TextArea")
        if text:
            self.setPlainText(text)


class PlainTextArea(QPlainTextEdit):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("PlainTextArea")
        if text:
            self.setPlainText(text)


class ComboSelect(QComboBox):
    def __init__(self, items: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ComboSelect")
        install_arrow_overlay(self, "dropdown")
        if items:
            self.addItems(items)


class EditableComboSelect(ComboSelect):
    def __init__(self, items: list[str] | None = None, parent=None):
        super().__init__(items, parent)
        self.setEditable(True)


class ToggleSwitch(QAbstractButton):
    checkedChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToggleSwitch")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(52, 28)
        self.toggled.connect(self.checkedChanged)
        self.toggled.connect(lambda checked: self.update())
        ThemeManager.instance().themeChanged.connect(self._on_theme_changed)

    def sizeHint(self):
        return QSize(52, 28)

    def _on_theme_changed(self, palette=None):
        self.update()

    def paintEvent(self, event):
        palette = ThemeManager.instance().palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        if not self.isEnabled():
            track_color = QColor(palette.disabled)
        else:
            track_color = QColor(palette.accent if self.isChecked() else palette.border)
        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(rect, 13, 13)

        knob_size = 22
        x = self.width() - knob_size - 4 if self.isChecked() else 4
        painter.setBrush(QColor(palette.surface))
        painter.setPen(QPen(QColor(0, 0, 0, 24), 1))
        painter.drawEllipse(QRectF(x, 3, knob_size, knob_size))


class RangeSlider(QSlider):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setObjectName("RangeSlider")


class ClickableSlider(RangeSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            span = self.width() if self.orientation() == Qt.Horizontal else self.height()
            position = (
                event.position().x()
                if self.orientation() == Qt.Horizontal
                else event.position().y()
            )
            ratio = max(0.0, min(1.0, position / max(1, span)))
            if self.orientation() == Qt.Vertical:
                ratio = 1.0 - ratio
            self.setValue(
                round(self.minimum() + (self.maximum() - self.minimum()) * ratio)
            )
        super().mousePressEvent(event)


__all__ = [
    "ClickableSlider",
    "ComboSelect",
    "DoubleNumberInput",
    "EditableComboSelect",
    "NumberInput",
    "PasswordInput",
    "PlainTextArea",
    "RangeSlider",
    "SearchInput",
    "TextArea",
    "TextInput",
    "ToggleSwitch",
]
