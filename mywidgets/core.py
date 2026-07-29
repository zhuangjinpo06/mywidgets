from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import weakref

import qtawesome as qta
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QFileDialog, QWidget

from .resource import DEFAULT_WINDOW_ICON, ICON_ALIASES, WINDOW_ICON_ALIASES
from .theme import ConfigStore, ThemeManager, ThemeMode, ThemePalette, apply_theme


@dataclass(frozen=True)
class IconSpec:
    name: str
    color_role: str = "text"


class IconResolver:
    _cache_limit = 256
    _cache: OrderedDict[tuple[str, str], QIcon] = OrderedDict()

    @staticmethod
    def resolve(name: str | IconSpec | QIcon | None, color_role: str = "text") -> QIcon:
        if isinstance(name, QIcon):
            return name

        if name is None:
            return QIcon()

        if isinstance(name, IconSpec):
            icon_name = name.name
            color_role = name.color_role
        else:
            icon_name = name

        icon_name = ICON_ALIASES.get(icon_name, icon_name)
        palette = ThemeManager.instance().palette
        color = getattr(palette, color_role, palette.text)
        key = (icon_name, color)
        cached = IconResolver._cache.get(key)
        if cached is not None:
            IconResolver._cache.move_to_end(key)
            return cached

        try:
            icon = qta.icon(icon_name, color=color)
        except (Exception, SystemExit):
            return QIcon()

        IconResolver._cache[key] = icon
        while len(IconResolver._cache) > IconResolver._cache_limit:
            IconResolver._cache.popitem(last=False)
        return icon


def _window_icon_spec(icon: str | IconSpec | QIcon | None):
    if isinstance(icon, str):
        return WINDOW_ICON_ALIASES.get(icon, icon)
    return icon or DEFAULT_WINDOW_ICON


def apply_window_icon(widget: QWidget, icon: str | IconSpec | QIcon | None = None, color_role: str = "accent"):
    widget.setWindowIcon(IconResolver.resolve(_window_icon_spec(icon), color_role))


def install_window_icon(widget: QWidget, icon: str | IconSpec | QIcon | None = None, color_role: str = "accent"):
    widget._mywidgets_window_icon = (icon, color_role)
    apply_window_icon(widget, icon, color_role)
    if getattr(widget, "_mywidgets_window_icon_bound", False):
        return

    widget_ref = weakref.ref(widget)

    def refresh(palette=None):
        target = widget_ref()
        if target is None:
            return
        try:
            current_icon, current_role = target._mywidgets_window_icon
            apply_window_icon(target, current_icon, current_role)
        except RuntimeError:
            return

    manager = ThemeManager.instance()
    manager.themeChanged.connect(refresh)

    def unbind(*args):
        try:
            manager.themeChanged.disconnect(refresh)
        except (RuntimeError, TypeError):
            pass

    widget.destroyed.connect(unbind)
    widget._mywidgets_window_icon_refresh = refresh
    widget._mywidgets_window_icon_bound = True


def create_existing_directory_dialog(parent: QWidget | None = None, title: str = "选择文件夹"):
    dialog = QFileDialog(parent, title)
    install_window_icon(dialog, "folder")
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    return dialog


def choose_existing_directory(parent: QWidget | None = None, title: str = "选择文件夹"):
    dialog = create_existing_directory_dialog(parent, title)
    try:
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return ""
        selected = dialog.selectedFiles()
        return selected[0] if selected else ""
    finally:
        dialog.deleteLater()


__all__ = [
    "ConfigStore",
    "IconResolver",
    "IconSpec",
    "ThemeManager",
    "ThemeMode",
    "ThemePalette",
    "apply_theme",
]
