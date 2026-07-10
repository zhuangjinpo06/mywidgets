from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QLabel, QProxyStyle, QStyle, QWidget

from .core import IconResolver
from .theme import ThemeManager, theme_qcolor


class FluentControlStyle(QProxyStyle):
    """Theme-aware primitives for controls whose native arrows are low contrast."""

    _ARROWS = {
        QStyle.PE_IndicatorArrowUp: "up",
        QStyle.PE_IndicatorArrowDown: "down",
        QStyle.PE_IndicatorArrowLeft: "left",
        QStyle.PE_IndicatorArrowRight: "right",
    }

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in (
            QStyle.PM_IndicatorWidth,
            QStyle.PM_IndicatorHeight,
            QStyle.PM_ExclusiveIndicatorWidth,
            QStyle.PM_ExclusiveIndicatorHeight,
        ):
            return 18
        return super().pixelMetric(metric, option, widget)

    def drawPrimitive(self, element, option, painter, widget=None):
        if element in self._ARROWS:
            self._draw_arrow(self._ARROWS[element], option, painter)
            return
        if element == QStyle.PE_IndicatorCheckBox:
            self._draw_checkbox(option, painter)
            return
        if element == QStyle.PE_IndicatorRadioButton:
            self._draw_radio(option, painter)
            return
        if element == QStyle.PE_FrameFocusRect and widget is not None:
            if widget.objectName() in {"CheckBox", "RadioButton"}:
                self._draw_focus(option, painter)
                return
        super().drawPrimitive(element, option, painter, widget)

    @staticmethod
    def _state_color(option, role: str = "text") -> QColor:
        palette = ThemeManager.instance().palette
        if not option.state & QStyle.State_Enabled:
            return theme_qcolor(palette.disabled)
        return theme_qcolor(getattr(palette, role, palette.text))

    def _draw_arrow(self, direction: str, option, painter):
        rect = QRectF(option.rect).adjusted(3, 3, -3, -3)
        center = rect.center()
        radius = max(2.5, min(rect.width(), rect.height()) * 0.28)
        if direction == "down":
            points = [QPointF(center.x() - radius, center.y() - radius / 2), QPointF(center.x(), center.y() + radius / 2), QPointF(center.x() + radius, center.y() - radius / 2)]
        elif direction == "up":
            points = [QPointF(center.x() - radius, center.y() + radius / 2), QPointF(center.x(), center.y() - radius / 2), QPointF(center.x() + radius, center.y() + radius / 2)]
        elif direction == "left":
            points = [QPointF(center.x() + radius / 2, center.y() - radius), QPointF(center.x() - radius / 2, center.y()), QPointF(center.x() + radius / 2, center.y() + radius)]
        else:
            points = [QPointF(center.x() - radius / 2, center.y() - radius), QPointF(center.x() + radius / 2, center.y()), QPointF(center.x() - radius / 2, center.y() + radius)]
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self._state_color(option), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(QPolygonF(points))
        painter.restore()

    def _draw_checkbox(self, option, painter):
        palette = ThemeManager.instance().palette
        rect = QRectF(option.rect).adjusted(1, 1, -1, -1)
        enabled = bool(option.state & QStyle.State_Enabled)
        checked = bool(option.state & QStyle.State_On)
        partial = bool(option.state & QStyle.State_NoChange)
        border = theme_qcolor(palette.accent if checked or partial else palette.border)
        fill = theme_qcolor(palette.accent if checked or partial else palette.input)
        if not enabled:
            border = theme_qcolor(palette.disabled)
            fill = theme_qcolor(palette.surface_alt)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 4, 4)
        if partial:
            painter.setPen(QPen(theme_qcolor(palette.on_accent), 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(rect.left() + 4, rect.center().y(), rect.right() - 4, rect.center().y())
        elif checked:
            path = QPainterPath()
            path.moveTo(rect.left() + 4, rect.center().y())
            path.lineTo(rect.center().x() - 1, rect.bottom() - 4)
            path.lineTo(rect.right() - 3, rect.top() + 4)
            painter.setPen(QPen(theme_qcolor(palette.on_accent), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        painter.restore()

    def _draw_radio(self, option, painter):
        palette = ThemeManager.instance().palette
        rect = QRectF(option.rect).adjusted(1, 1, -1, -1)
        enabled = bool(option.state & QStyle.State_Enabled)
        checked = bool(option.state & QStyle.State_On)
        border = theme_qcolor(palette.accent if checked else palette.border)
        fill = theme_qcolor(palette.input if enabled else palette.surface_alt)
        if not enabled:
            border = theme_qcolor(palette.disabled)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawEllipse(rect)
        if checked:
            inner = rect.adjusted(4, 4, -4, -4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(theme_qcolor(palette.accent if enabled else palette.disabled))
            painter.drawEllipse(inner)
        painter.restore()

    def _draw_focus(self, option, painter):
        palette = ThemeManager.instance().palette
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(theme_qcolor(palette.focus), 1.2, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(option.rect).adjusted(1, 1, -1, -1), 4, 4)
        painter.restore()


def install_control_style(widget: QWidget):
    if getattr(widget, "_fluent_control_style", None) is not None:
        return
    style = FluentControlStyle()
    widget._fluent_control_style = style
    widget.setStyle(style)


def reinstall_control_style(widget: QWidget):
    old_style = getattr(widget, "_fluent_control_style", None)
    widget.setStyle(None)
    widget._fluent_control_style = None
    install_control_style(widget)
    if old_style is not None:
        old_style.deleteLater()
    widget.update()


class ControlArrowOverlay(QObject):
    def __init__(self, widget: QWidget, mode: str):
        super().__init__(widget)
        self.widget = widget
        self.mode = mode
        self.labels: list[QLabel] = []
        names = ["chevron_down"] if mode == "dropdown" else ["chevron_up", "chevron_down"]
        for name in names:
            label = QLabel(widget)
            label.setAlignment(Qt.AlignCenter)
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
            label.setProperty("iconName", name)
            self.labels.append(label)
        widget.installEventFilter(self)
        ThemeManager.instance().themeChanged.connect(self._refresh_icons)
        self._refresh_icons()
        self._position()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.Show):
            self._position()
        elif event.type() == QEvent.EnabledChange:
            self._refresh_icons()
        return False

    def _refresh_icons(self, palette=None):
        role = "text" if self.widget.isEnabled() else "disabled"
        for label in self.labels:
            label.setPixmap(
                IconResolver.resolve(label.property("iconName"), role).pixmap(11, 11)
            )
            label.raise_()

    def _position(self):
        width = self.widget.width()
        height = self.widget.height()
        if not self.labels or width <= 0 or height <= 0:
            return
        if self.mode == "dropdown":
            self.labels[0].setGeometry(max(0, width - 28), 0, 24, height)
        else:
            half = max(1, height // 2)
            self.labels[0].setGeometry(max(0, width - 24), 1, 20, max(1, half - 1))
            self.labels[1].setGeometry(max(0, width - 24), half, 20, max(1, height - half - 1))
        for label in self.labels:
            label.raise_()


def install_arrow_overlay(widget: QWidget, mode: str = "spin"):
    if getattr(widget, "_fluent_arrow_overlay", None) is None:
        widget._fluent_arrow_overlay = ControlArrowOverlay(widget, mode)


__all__ = []
