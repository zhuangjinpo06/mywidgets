from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QRadioButton,
    QSizePolicy,
)

from .core import IconResolver, IconSpec
from .control_style import install_control_style, reinstall_control_style
from .theme import ThemeManager


IconLike = str | IconSpec | QIcon | None


class _ThemedButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        icon: IconLike = None,
        icon_role: str = "text",
        parent=None,
    ):
        super().__init__(text, parent)
        self._icon_spec = icon
        self._icon_role = icon_role
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(16, 16))
        ThemeManager.instance().themeChanged.connect(self._refresh_icon)
        self._refresh_icon()

    def set_icon(self, icon: IconLike, color_role: str | None = None):
        self._icon_spec = icon
        if color_role is not None:
            self._icon_role = color_role
        self._refresh_icon()

    def _refresh_icon(self, palette=None):
        icon = IconResolver.resolve(self._icon_spec, self._icon_role)
        self.setIcon(icon)


class PrimaryButton(_ThemedButton):
    def __init__(self, text: str, icon: IconLike = None, parent=None):
        super().__init__(text, icon, "on_accent", parent)
        self.setObjectName("PrimaryButton")


class SecondaryButton(_ThemedButton):
    def __init__(self, text: str, icon: IconLike = None, parent=None):
        super().__init__(text, icon, "text", parent)
        self.setObjectName("SecondaryButton")


class TransparentButton(_ThemedButton):
    def __init__(self, text: str, icon: IconLike = None, parent=None):
        super().__init__(text, icon, "text", parent)
        self.setObjectName("TransparentButton")


class ToggleButton(_ThemedButton):
    def __init__(self, text: str, icon: IconLike = None, parent=None):
        super().__init__(text, icon, "text", parent)
        self.setObjectName("ToggleButton")
        self.setCheckable(True)


class HyperlinkButton(_ThemedButton):
    def __init__(self, text: str, url: str = "", icon: IconLike = "link", parent=None):
        super().__init__(text, icon, "accent", parent)
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        self.setObjectName("HyperlinkButton")
        self.url = url
        self.clicked.connect(
            lambda checked=False: QDesktopServices.openUrl(QUrl(self.url)) if self.url else None
        )


class IconButton(_ThemedButton):
    def __init__(self, icon: IconLike, tooltip: str = "", parent=None):
        super().__init__("", icon, "text", parent)
        self.setObjectName("IconButton")
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)


class ToolButton(IconButton):
    def __init__(self, icon: IconLike, tooltip: str = "", parent=None):
        super().__init__(icon, tooltip, parent)
        self.setObjectName("ToolButton")


class PrimaryToolButton(IconButton):
    def __init__(self, icon: IconLike, tooltip: str = "", parent=None):
        super().__init__(icon, tooltip, parent)
        self._icon_role = "on_accent"
        self.setObjectName("PrimaryToolButton")
        self._refresh_icon()


class TransparentToolButton(IconButton):
    def __init__(self, icon: IconLike, tooltip: str = "", parent=None):
        super().__init__(icon, tooltip, parent)
        self.setObjectName("TransparentToolButton")


class ToggleToolButton(ToolButton):
    def __init__(self, icon: IconLike, tooltip: str = "", parent=None):
        super().__init__(icon, tooltip, parent)
        self.setObjectName("ToggleToolButton")
        self.setCheckable(True)


class CheckBox(QCheckBox):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("CheckBox")
        self.setCursor(Qt.PointingHandCursor)
        install_control_style(self)
        ThemeManager.instance().themeChanged.connect(self._refresh_control_style)

    def _refresh_control_style(self, palette=None):
        reinstall_control_style(self)


class RadioButton(QRadioButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("RadioButton")
        self.setCursor(Qt.PointingHandCursor)
        install_control_style(self)
        ThemeManager.instance().themeChanged.connect(self._refresh_control_style)

    def _refresh_control_style(self, palette=None):
        reinstall_control_style(self)


class DropDownButton(_ThemedButton):
    menuRequested = Signal()

    def __init__(
        self,
        text: str,
        icon: IconLike = None,
        menu: QMenu | None = None,
        parent=None,
        *,
        _primary: bool = False,
    ):
        super().__init__(text, icon, "on_accent" if _primary else "text", parent)
        self.setObjectName("PrimaryDropDownButton" if _primary else "DropDownButton")
        self._menu = menu
        self.clicked.connect(self._show_menu)

    def set_menu(self, menu: QMenu | None):
        self._menu = menu

    def menu(self) -> QMenu | None:
        return self._menu

    def _show_menu(self):
        if self._menu is None:
            self.menuRequested.emit()
            return
        self._menu.popup(self.mapToGlobal(self.rect().bottomLeft()))


class PrimaryDropDownButton(DropDownButton):
    def __init__(self, text: str, icon: IconLike = None, menu: QMenu | None = None, parent=None):
        super().__init__(text, icon, menu, parent, _primary=True)


class SplitButton(QFrame):
    clicked = Signal()
    menuRequested = Signal()

    def __init__(
        self,
        text: str,
        icon: IconLike = None,
        menu: QMenu | None = None,
        parent=None,
        *,
        _primary: bool = False,
    ):
        super().__init__(parent)
        self.setObjectName("SplitButton")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._menu = menu
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.action_button = _ThemedButton(
            text,
            icon,
            "on_accent" if _primary else "text",
            self,
        )
        self.action_button.setObjectName(
            "PrimarySplitButtonAction" if _primary else "SplitButtonAction"
        )
        self.menu_button = _ThemedButton(
            "",
            "chevron_down",
            "on_accent" if _primary else "text",
            self,
        )
        self.menu_button.setObjectName(
            "PrimarySplitButtonMenu" if _primary else "SplitButtonMenu"
        )
        self.menu_button.setAccessibleName("更多选项")
        self.menu_button.setToolTip("更多选项")
        self.action_button.clicked.connect(self.clicked)
        self.menu_button.clicked.connect(self._show_menu)
        layout.addWidget(self.action_button)
        layout.addWidget(self.menu_button)

    def set_menu(self, menu: QMenu | None):
        self._menu = menu

    def menu(self) -> QMenu | None:
        return self._menu

    def _show_menu(self):
        if self._menu is None:
            self.menuRequested.emit()
            return
        self._menu.popup(
            self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        )


class PrimarySplitButton(SplitButton):
    def __init__(self, text: str, icon: IconLike = None, menu: QMenu | None = None, parent=None):
        super().__init__(text, icon, menu, parent, _primary=True)


class PillButton(ToggleButton):
    def __init__(self, text: str, icon: IconLike = None, parent=None):
        super().__init__(text, icon, parent)
        self.setObjectName("PillButton")


__all__ = [
    "CheckBox",
    "DropDownButton",
    "HyperlinkButton",
    "IconButton",
    "PillButton",
    "PrimaryButton",
    "PrimaryDropDownButton",
    "PrimarySplitButton",
    "PrimaryToolButton",
    "RadioButton",
    "SecondaryButton",
    "SplitButton",
    "ToggleButton",
    "ToggleToolButton",
    "ToolButton",
    "TransparentButton",
    "TransparentToolButton",
]
