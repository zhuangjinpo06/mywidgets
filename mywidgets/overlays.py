from __future__ import annotations

from PySide6.QtCore import QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from .buttons import PrimaryButton, SecondaryButton, ToolButton
from .core import IconResolver, choose_existing_directory, install_window_icon
from .enums import PopupPosition, StatusKind, enum_value
from .feedback import StateTooltip, Toast, ToastManager
from .theme import ThemeManager
from .typography import CaptionText, StrongText


class ModernMenu(QMenu):
    def __init__(self, title: str = "", parent=None):
        super().__init__(title, parent)
        self.setObjectName("ModernMenu")
        self._icon_specs: dict[QAction, object] = {}
        install_window_icon(self, "menu")
        ThemeManager.instance().themeChanged.connect(self._refresh_icons)

    def add_command(self, text: str, icon=None, callback=None) -> QAction:
        action = QAction(IconResolver.resolve(icon), text, self)
        if callback:
            action.triggered.connect(callback)
        self.addAction(action)
        self._icon_specs[action] = icon
        return action

    def _refresh_icons(self, palette=None):
        for action, icon in list(self._icon_specs.items()):
            try:
                action.setIcon(IconResolver.resolve(icon))
            except RuntimeError:
                self._icon_specs.pop(action, None)

    def clear(self):
        super().clear()
        self._icon_specs.clear()


class CheckableMenu(ModernMenu):
    currentChanged = Signal(str)

    def __init__(self, title: str = "", exclusive: bool = False, parent=None):
        super().__init__(title, parent)
        self.group = QActionGroup(self)
        self.group.setExclusive(exclusive)

    def add_checkable(self, text: str, checked: bool = False, icon=None):
        action = QAction(IconResolver.resolve(icon), text, self)
        action.setCheckable(True)
        action.setChecked(checked)
        action.toggled.connect(
            lambda active, value=text: self.currentChanged.emit(value) if active else None
        )
        self.group.addAction(action)
        self.addAction(action)
        self._icon_specs[action] = icon
        return action


class ModernDialog(QDialog):
    def __init__(self, title: str, content: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("ModernDialog")
        self.setWindowTitle(title)
        install_window_icon(self, "dialog")
        self.setModal(True)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addWidget(StrongText(title))
        if content:
            label = CaptionText(content)
            label.setWordWrap(True)
            layout.addWidget(label)
        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        layout.addLayout(self.body)
        self.footer = QHBoxLayout()
        self.footer.addStretch(1)
        layout.addLayout(self.footer)

    def add_widget(self, widget: QWidget):
        self.body.addWidget(widget)
        return widget

    def add_button(self, text: str, role: str = "secondary"):
        button = PrimaryButton(text) if role == "primary" else SecondaryButton(text)
        self.footer.addWidget(button)
        return button


class MessageBox(ModernDialog):
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(title, content, parent)
        install_window_icon(self, "message")
        cancel = self.add_button("取消")
        ok = self.add_button("确定", "primary")
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)


class Flyout(QFrame):
    closed = Signal()

    def __init__(self, title: str, content: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Flyout")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        install_window_icon(self, "flyout")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(220)
        self.setMaximumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.addWidget(StrongText(title))
        if content:
            label = CaptionText(content)
            label.setWordWrap(True)
            layout.addWidget(label)

    @classmethod
    def show_at(
        cls,
        anchor: QWidget,
        title: str,
        content: str = "",
        position: PopupPosition | str = PopupPosition.BOTTOM,
    ):
        flyout = cls(title, content, anchor.window())
        flyout.adjustSize()
        popup_position = enum_value(position, PopupPosition, PopupPosition.BOTTOM)
        anchor_top_left = anchor.mapToGlobal(QPoint(0, 0))
        gap = 8
        if popup_position in (
            PopupPosition.TOP_LEFT,
            PopupPosition.TOP,
            PopupPosition.TOP_RIGHT,
        ):
            if popup_position == PopupPosition.TOP_LEFT:
                x = anchor_top_left.x()
            elif popup_position == PopupPosition.TOP_RIGHT:
                x = anchor_top_left.x() + anchor.width() - flyout.width()
            else:
                x = anchor_top_left.x() + (anchor.width() - flyout.width()) // 2
            pos = QPoint(
                x,
                anchor_top_left.y() - flyout.height() - gap,
            )
        elif popup_position == PopupPosition.LEFT:
            pos = QPoint(
                anchor_top_left.x() - flyout.width() - gap,
                anchor_top_left.y() + (anchor.height() - flyout.height()) // 2,
            )
        elif popup_position == PopupPosition.RIGHT:
            pos = QPoint(
                anchor_top_left.x() + anchor.width() + gap,
                anchor_top_left.y() + (anchor.height() - flyout.height()) // 2,
            )
        elif popup_position in (
            PopupPosition.BOTTOM_LEFT,
            PopupPosition.BOTTOM,
            PopupPosition.BOTTOM_RIGHT,
        ):
            if popup_position == PopupPosition.BOTTOM_LEFT:
                x = anchor_top_left.x()
            elif popup_position == PopupPosition.BOTTOM_RIGHT:
                x = anchor_top_left.x() + anchor.width() - flyout.width()
            else:
                x = anchor_top_left.x() + (anchor.width() - flyout.width()) // 2
            pos = QPoint(
                x,
                anchor_top_left.y() + anchor.height() + gap,
            )
        else:
            pos = QPoint(
                anchor_top_left.x() + (anchor.width() - flyout.width()) // 2,
                anchor_top_left.y() + (anchor.height() - flyout.height()) // 2,
            )
        screen = anchor.screen() or QApplication.screenAt(anchor_top_left)
        if screen is not None:
            available = screen.availableGeometry()
            pos.setX(max(available.left(), min(pos.x(), available.right() - flyout.width() + 1)))
            pos.setY(max(available.top(), min(pos.y(), available.bottom() - flyout.height() + 1)))
        flyout.move(pos)
        flyout.show()
        return flyout

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class TeachingTip(Flyout):
    def __init__(self, title: str, content: str = "", parent=None):
        super().__init__(title, content, parent)
        self.setObjectName("TeachingTip")
        install_window_icon(self, "warning")


class TooltipLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("role", "caption")
        self.setWordWrap(True)


class InfoBanner(QFrame):
    closed = Signal()

    def __init__(
        self,
        title: str,
        content: str = "",
        icon: str = "info",
        parent=None,
        *,
        kind: StatusKind | str | None = None,
        closable: bool = False,
        duration: int = 0,
    ):
        super().__init__(parent)
        inferred = kind or (icon if icon in {item.value for item in StatusKind} else StatusKind.INFO)
        self.kind = enum_value(inferred, StatusKind, StatusKind.INFO)
        self._icon_name = icon
        self.setObjectName("InfoBanner")
        self.setProperty("kind", self.kind.value)
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        self.icon_label = QLabel()
        layout.addWidget(self.icon_label)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.addWidget(StrongText(title))
        if content:
            label = CaptionText(content)
            label.setWordWrap(True)
            text_layout.addWidget(label)
        layout.addLayout(text_layout, 1)
        if closable:
            close_button = ToolButton("close", "关闭")
            close_button.clicked.connect(self.close)
            layout.addWidget(close_button)
        ThemeManager.instance().themeChanged.connect(self._refresh_icon)
        self._refresh_icon()
        if duration > 0:
            self._close_timer.start(duration)

    def _refresh_icon(self, palette=None):
        role = {
            StatusKind.SUCCESS: "success",
            StatusKind.WARNING: "warning",
            StatusKind.ERROR: "danger",
        }.get(self.kind, "info")
        self.icon_label.setPixmap(IconResolver.resolve(self._icon_name, role).pixmap(20, 20))

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class ColorDialog(QColorDialog):
    colorChanged = Signal(str)

    def __init__(self, color: str = "#3f8cff", parent=None):
        super().__init__(QColor(color), parent)
        self.setObjectName("ColorDialog")
        self.setWindowTitle("选择颜色")
        install_window_icon(self, "color")
        self.currentColorChanged.connect(
            lambda selected: self.colorChanged.emit(selected.name())
        )


class FolderListDialog(ModernDialog):
    pathsChanged = Signal(list)

    def __init__(self, title: str = "文件夹", paths: list[str] | None = None, parent=None):
        super().__init__(title, "添加或移除文件夹路径。", parent)
        install_window_icon(self, "folder")
        self.list_widget = QListWidget(self)
        self.list_widget.setObjectName("ModernList")
        self.list_widget.addItems(paths or [])
        self.add_widget(self.list_widget)
        add_button = self.add_button("添加")
        remove_button = self.add_button("移除")
        done_button = self.add_button("完成", "primary")
        add_button.clicked.connect(self.choose_folder)
        remove_button.clicked.connect(self.remove_selected)
        done_button.clicked.connect(self.accept)

    def paths(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def choose_folder(self):
        path = choose_existing_directory(self, "选择文件夹")
        if path and path not in self.paths():
            self.list_widget.addItem(path)
            self.pathsChanged.emit(self.paths())

    def remove_selected(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)
            self.pathsChanged.emit(self.paths())


__all__ = [
    "CheckableMenu",
    "ColorDialog",
    "Flyout",
    "FolderListDialog",
    "InfoBanner",
    "MessageBox",
    "ModernDialog",
    "ModernMenu",
    "StateTooltip",
    "TeachingTip",
    "Toast",
    "ToastManager",
    "TooltipLabel",
]
