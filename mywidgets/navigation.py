from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .core import IconResolver, install_window_icon
from .data import SegmentedControl
from .enums import NavigationPosition, enum_value
from .theme import ThemeManager
from .typography import CaptionText, StrongText


class NavItem(QPushButton):
    selected = Signal(int)

    def __init__(self, index: int, title: str, icon: str, parent=None):
        super().__init__(title, parent)
        self.index = index
        self.title = title
        self._icon_name = icon
        self.setObjectName("NavItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(18, 18))
        self.clicked.connect(lambda checked=False: self.selected.emit(self.index))
        ThemeManager.instance().themeChanged.connect(self._refresh_icon)
        self._refresh_icon()

    def set_compact(self, compact: bool):
        self.setProperty("compact", "true" if compact else "false")
        self.setText("" if compact else self.title)
        self.setToolTip(self.title if compact else "")
        self.style().unpolish(self)
        self.style().polish(self)

    def _refresh_icon(self, palette=None):
        role = "accent" if self.isChecked() else "muted"
        self.setIcon(IconResolver.resolve(self._icon_name, role))


class NavigationHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("NavigationHeader")


class NavigationSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavigationSeparator")
        self.setFixedHeight(1)


class SideNavigation(QWidget):
    currentChanged = Signal(int)

    def __init__(self, brand: str = "API Studio", parent=None):
        super().__init__(parent)
        self.setObjectName("SideNavigation")
        self._expanded_width = 220
        self._compact = False
        self.setFixedWidth(self._expanded_width)
        self._items: list[NavItem] = []
        self._extras: list[QWidget] = []

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 18, 18, 18)
        self.root.setSpacing(10)
        self.brand_label = QLabel(brand)
        self.brand_label.setProperty("role", "brand")
        self.root.addWidget(self.brand_label)
        self.root.addSpacing(8)
        self.top_layout = QVBoxLayout()
        self.top_layout.setSpacing(6)
        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.setSpacing(6)
        self.root.addLayout(self.top_layout)
        self.root.addStretch(1)
        self.root.addLayout(self.bottom_layout)

    def _target_layout(self, position):
        value = enum_value(position, NavigationPosition, NavigationPosition.TOP)
        return self.bottom_layout if value == NavigationPosition.BOTTOM else self.top_layout

    def add_item(
        self,
        index: int,
        title: str,
        icon: str,
        position: NavigationPosition | str = NavigationPosition.TOP,
    ) -> NavItem:
        item = NavItem(index, title, icon, self)
        item.set_compact(self._compact)
        item.selected.connect(self.set_current)
        item.selected.connect(self.currentChanged)
        self._items.append(item)
        self._target_layout(position).addWidget(item)
        if len(self._items) == 1:
            item.setChecked(True)
            item._refresh_icon()
        return item

    def add_header(self, text: str, position: NavigationPosition | str = NavigationPosition.TOP):
        header = NavigationHeader(text, self)
        self._extras.append(header)
        self._target_layout(position).addWidget(header)
        header.setVisible(not self._compact)
        return header

    def add_separator(self, position: NavigationPosition | str = NavigationPosition.TOP):
        separator = NavigationSeparator(self)
        self._extras.append(separator)
        self._target_layout(position).addWidget(separator)
        return separator

    def remove_item(self, index: int):
        item = next((candidate for candidate in self._items if candidate.index == index), None)
        if item is None:
            return None
        self._items.remove(item)
        item.setParent(None)
        item.deleteLater()
        for candidate in self._items:
            if candidate.index > index:
                candidate.index -= 1
        if self._items and not any(candidate.isChecked() for candidate in self._items):
            self.set_current(min(index, len(self._items) - 1))
        return item

    def clear(self):
        for item in list(self._items):
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        for extra in self._extras:
            extra.setParent(None)
            extra.deleteLater()
        self._extras.clear()

    def set_current(self, index: int):
        found = False
        for item in self._items:
            selected = item.index == index
            item.setChecked(selected)
            item._refresh_icon()
            found = found or selected
        return found

    def set_compact(self, compact: bool):
        self._compact = bool(compact)
        self.setFixedWidth(72 if self._compact else self._expanded_width)
        self.root.setContentsMargins(10 if self._compact else 18, 18, 10 if self._compact else 18, 18)
        self.brand_label.setVisible(not self._compact)
        for item in self._items:
            item.set_compact(self._compact)
        for extra in self._extras:
            if isinstance(extra, NavigationHeader):
                extra.setVisible(not self._compact)

    def is_compact(self):
        return self._compact


class NavigationUserCard(QWidget):
    def __init__(self, name: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.addWidget(StrongText(name))
        if subtitle:
            layout.addWidget(CaptionText(subtitle))


class TopNavigation(QWidget):
    currentChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[NavItem] = []
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)

    def add_item(self, title: str, icon: str) -> NavItem:
        item = NavItem(len(self._items), title, icon, self)
        item.selected.connect(self.set_current)
        item.selected.connect(self.currentChanged)
        self._items.append(item)
        self.layout.addWidget(item)
        if len(self._items) == 1:
            item.setChecked(True)
            item._refresh_icon()
        return item

    def remove_item(self, index: int):
        if not 0 <= index < len(self._items):
            return None
        item = self._items.pop(index)
        item.deleteLater()
        for new_index, candidate in enumerate(self._items):
            candidate.index = new_index
        if self._items:
            self.set_current(min(index, len(self._items) - 1))
        return item

    def clear(self):
        while self._items:
            self.remove_item(len(self._items) - 1)

    def set_current(self, index: int):
        if not 0 <= index < len(self._items):
            return False
        for item in self._items:
            item.setChecked(item.index == index)
            item._refresh_icon()
        return True


class PivotControl(SegmentedControl):
    def __init__(self, items: list[str] | None = None, parent=None):
        super().__init__(items, parent)
        self.setObjectName("PivotControl")


class ModernWindow(QMainWindow):
    currentChanged = Signal(int)

    def __init__(self, title: str = "Modern App", brand: str = "API Studio", parent=None):
        super().__init__(parent)
        self.setObjectName("ModernWindow")
        self.setWindowTitle(title)
        install_window_icon(self, "app")
        self.root = QWidget()
        self.root.setObjectName("AppRoot")
        self.setCentralWidget(self.root)
        layout = QHBoxLayout(self.root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.navigation = SideNavigation(brand, self.root)
        self.stack = QStackedWidget(self.root)
        self.stack.setObjectName("ContentStack")
        self._routes: list[str] = []
        layout.addWidget(self.navigation)
        layout.addWidget(self.stack, 1)
        self.navigation.currentChanged.connect(self.set_current)

    def add_page(
        self,
        widget: QWidget,
        title: str,
        icon: str,
        position: NavigationPosition | str = NavigationPosition.TOP,
        route_key: str | None = None,
    ) -> int:
        index = self.stack.count()
        route = route_key or widget.objectName() or f"page_{index}"
        if route in self._routes:
            raise ValueError(f"Duplicate route key: {route}")
        index = self.stack.addWidget(widget)
        self._routes.append(route)
        self.navigation.add_item(index, title, icon, position)
        if index == 0:
            self.stack.setCurrentIndex(0)
        return index

    def set_current(self, route_or_index: str | int):
        if isinstance(route_or_index, str):
            if route_or_index not in self._routes:
                return False
            index = self._routes.index(route_or_index)
        else:
            index = int(route_or_index)
        if not 0 <= index < self.stack.count():
            return False
        changed = self.stack.currentIndex() != index
        self.stack.setCurrentIndex(index)
        self.navigation.set_current(index)
        if changed:
            self.currentChanged.emit(index)
        return True

    def remove_page(self, route_or_index: str | int):
        if isinstance(route_or_index, str):
            if route_or_index not in self._routes:
                return None
            index = self._routes.index(route_or_index)
        else:
            index = int(route_or_index)
        if not 0 <= index < self.stack.count():
            return None
        widget = self.stack.widget(index)
        self.stack.removeWidget(widget)
        self._routes.pop(index)
        self.navigation.remove_item(index)
        if self.stack.count():
            self.set_current(min(index, self.stack.count() - 1))
        return widget

    def route_key(self, index: int):
        return self._routes[index] if 0 <= index < len(self._routes) else None


class SplashScreen(QWidget):
    def __init__(self, title: str = "正在启动", icon: str = "rocket", parent=None):
        super().__init__(parent)
        self.setObjectName("SplashScreen")
        self._icon_name = icon
        self.setAttribute(Qt.WA_StyledBackground, True)
        if parent is None:
            self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        else:
            parent.installEventFilter(self)
            self.setGeometry(parent.rect())
        install_window_icon(self, "splash")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.title_label = StrongText(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setObjectName("IndeterminateProgressLine")
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(220)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.progress)
        ThemeManager.instance().themeChanged.connect(self._refresh_icon)
        self._refresh_icon()

    def _refresh_icon(self, palette=None):
        self.icon_label.setPixmap(
            IconResolver.resolve(self._icon_name, "accent").pixmap(48, 48)
        )

    def eventFilter(self, watched, event):
        if watched is self.parentWidget() and event.type() == QEvent.Resize:
            self.setGeometry(watched.rect())
        return False

    def finish(self, window: QWidget | None = None):
        self.close()
        if window is not None:
            window.show()


__all__ = [
    "ModernWindow",
    "NavItem",
    "NavigationHeader",
    "NavigationSeparator",
    "NavigationUserCard",
    "PivotControl",
    "SideNavigation",
    "SplashScreen",
    "TopNavigation",
]
