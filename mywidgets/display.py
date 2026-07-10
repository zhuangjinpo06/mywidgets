from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .buttons import ToolButton
from .core import IconResolver, IconSpec
from .enums import StatusKind, enum_value
from .theme import ThemeManager, theme_qcolor
from .typography import BodyText, CaptionText, StrongText


class InfoBadge(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("InfoBadge")
        self.setAlignment(Qt.AlignCenter)


class StatusBadge(QLabel):
    def __init__(self, text: str, kind: StatusKind | str = StatusKind.INFO, parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusBadge")
        self.setAlignment(Qt.AlignCenter)
        self.set_kind(kind)

    def set_kind(self, kind: StatusKind | str):
        self.kind = enum_value(kind, StatusKind, StatusKind.INFO)
        self.setProperty("kind", self.kind.value)
        self.style().unpolish(self)
        self.style().polish(self)


class DotBadge(StatusBadge):
    def __init__(self, kind: StatusKind | str = StatusKind.INFO, parent=None):
        super().__init__("", kind, parent)
        self.setObjectName("DotBadge")
        self.setFixedSize(10, 10)


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)


class Panel(Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")


class ClickableCard(Card):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ClickableCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class ElevatedCard(ClickableCard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ElevatedCard")
        self._effect = QGraphicsDropShadowEffect(self)
        self._effect.setBlurRadius(24)
        self._effect.setOffset(0, 6)
        self.setGraphicsEffect(self._effect)
        ThemeManager.instance().themeChanged.connect(self._refresh_shadow)
        self._refresh_shadow()

    def _refresh_shadow(self, palette=None):
        self._effect.setColor(theme_qcolor(ThemeManager.instance().palette.shadow))


class HeaderCard(Card):
    def __init__(self, title: str, content: str = "", icon: str | IconSpec | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderCard")
        self._icon_spec = icon
        self.icon_label = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        header = QFrame(self)
        header.setObjectName("HeaderCardHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        if icon:
            self.icon_label = QLabel(header)
            header_layout.addWidget(self.icon_label)
        header_layout.addWidget(StrongText(title), 1)
        root.addWidget(header)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(16, 14, 16, 16)
        self.body.setSpacing(10)
        if content:
            label = BodyText(content)
            label.setWordWrap(True)
            self.body.addWidget(label)
        root.addLayout(self.body)
        if self.icon_label is not None:
            ThemeManager.instance().themeChanged.connect(self._refresh_icon)
            self._refresh_icon()

    def add_widget(self, widget: QWidget):
        self.body.addWidget(widget)
        return widget

    def _refresh_icon(self, palette=None):
        if self.icon_label is not None:
            self.icon_label.setPixmap(
                IconResolver.resolve(self._icon_spec, "accent").pixmap(18, 18)
            )


class HorizontalSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HorizontalSeparator")
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)


class VerticalSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VerticalSeparator")
        self.setFrameShape(QFrame.VLine)
        self.setFixedWidth(1)


class ProgressLine(QProgressBar):
    def __init__(self, value: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("ProgressLine")
        self.setRange(0, 100)
        self.setValue(value)
        self.setTextVisible(False)


class IndeterminateProgressLine(ProgressLine):
    def __init__(self, parent=None):
        super().__init__(0, parent)
        self.setObjectName("IndeterminateProgressLine")
        self.setRange(0, 0)


class ProgressRing(QProgressBar):
    def __init__(self, value: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("ProgressRing")
        self.setRange(0, 100)
        self.setValue(value)
        self.setFixedSize(64, 64)
        self.setTextVisible(False)
        ThemeManager.instance().themeChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self, palette=None):
        self.update()

    def paintEvent(self, event):
        palette = ThemeManager.instance().palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(6, 6, -6, -6)
        span = -round(360 * 16 * self.value() / max(1, self.maximum()))
        painter.setPen(QPen(QColor(palette.surface_alt), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(QPen(QColor(palette.accent), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, span)
        painter.setPen(QColor(palette.text))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value()}%")


class IndeterminateProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IndeterminateProgressRing")
        self.setFixedSize(36, 36)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._advance)

    def _advance(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def showEvent(self, event):
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = ThemeManager.instance().palette
        painter.setPen(QPen(QColor(palette.accent), 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(self.rect().adjusted(4, 4, -4, -4), self._angle * 16, 110 * 16)


class ImageView(QLabel):
    def __init__(self, source: str | Path | QPixmap | QImage | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ImageView")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(48, 48)
        self._source = QPixmap()
        if source is not None:
            self.set_source(source)

    def set_source(self, source: str | Path | QPixmap | QImage):
        if isinstance(source, QPixmap):
            self._source = source
        elif isinstance(source, QImage):
            self._source = QPixmap.fromImage(source)
        else:
            self._source = QPixmap(str(source))
        self._update_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        if not self._source.isNull():
            self.setPixmap(
                self._source.scaled(
                    self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )


class Avatar(QWidget):
    def __init__(
        self,
        text: str = "",
        image: str | Path | QPixmap | None = None,
        diameter: int = 40,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("Avatar")
        self.text = text
        self._pixmap = image if isinstance(image, QPixmap) else QPixmap(str(image)) if image else QPixmap()
        self.setFixedSize(diameter, diameter)
        ThemeManager.instance().themeChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self, palette=None):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(QRectF(self.rect()))
        painter.setClipPath(path)
        if not self._pixmap.isNull():
            pixmap = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            painter.drawPixmap(self.rect(), pixmap)
            return
        palette = ThemeManager.instance().palette
        painter.fillPath(path, theme_qcolor(palette.accent_soft))
        painter.setClipping(False)
        painter.setPen(QColor(palette.accent))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text[:2].upper())


class MetricCard(Card):
    def __init__(self, icon: str, title: str, value: str, detail: str, progress: int, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(138)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        top_row = QHBoxLayout()
        icon_button = ToolButton(icon)
        icon_button.setObjectName("MetricIcon")
        icon_button.setEnabled(False)
        title_label = CaptionText(title)
        top_row.addWidget(icon_button)
        top_row.addWidget(title_label)
        top_row.addStretch(1)
        value_label = QLabel(value)
        value_label.setProperty("role", "pageTitle")
        detail_label = CaptionText(detail)
        detail_label.setWordWrap(True)
        layout.addLayout(top_row)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)
        layout.addWidget(ProgressLine(progress))


class EmptyState(Card):
    def __init__(self, title: str, message: str = "", icon: str = "info", parent=None):
        super().__init__(parent)
        self._icon_name = icon
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        label = StrongText(title)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        if message:
            caption = CaptionText(message)
            caption.setAlignment(Qt.AlignCenter)
            caption.setWordWrap(True)
            layout.addWidget(caption)
        ThemeManager.instance().themeChanged.connect(self._refresh_icon)
        self._refresh_icon()

    def _refresh_icon(self, palette=None):
        self.icon_label.setPixmap(IconResolver.resolve(self._icon_name, "muted").pixmap(36, 36))


class LoadingPanel(Card):
    def __init__(self, text: str = "加载中", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(IndeterminateProgressRing())
        label = BodyText(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch(1)


__all__ = [
    "Avatar",
    "Card",
    "ClickableCard",
    "DotBadge",
    "ElevatedCard",
    "EmptyState",
    "HeaderCard",
    "HorizontalSeparator",
    "ImageView",
    "IndeterminateProgressLine",
    "IndeterminateProgressRing",
    "InfoBadge",
    "LoadingPanel",
    "MetricCard",
    "Panel",
    "ProgressLine",
    "ProgressRing",
    "StatusBadge",
    "VerticalSeparator",
]
