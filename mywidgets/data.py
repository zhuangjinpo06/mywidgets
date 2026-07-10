from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QListView,
    QListWidget,
    QMenu,
    QPushButton,
    QScrollArea,
    QTableView,
    QTableWidget,
    QTabWidget,
    QTreeView,
    QTreeWidget,
    QWidget,
)

from .buttons import PrimaryButton, SecondaryButton, ToolButton, TransparentButton
from .core import IconResolver, IconSpec, install_window_icon
from .theme import ThemeManager
from .typography import BodyText, CaptionText


class DataTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DataTable")
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(False)


class ModernList(QListWidget):
    def __init__(self, items: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernList")
        self.setAlternatingRowColors(True)
        if items:
            self.addItems(items)


class ModernTree(QTreeWidget):
    def __init__(self, headers: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernTree")
        self.setAlternatingRowColors(True)
        if headers:
            self.setHeaderLabels(headers)


class ModernListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernListView")
        self.setAlternatingRowColors(True)
        self.setUniformItemSizes(True)


class ModernTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernTreeView")
        self.setAlternatingRowColors(True)


class DataTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DataTableView")
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)


class ModernTabs(QTabWidget):
    tabClosed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernTabs")
        self.setDocumentMode(True)
        self.tabCloseRequested.connect(self._close_tab)

    def set_tabs_closable(self, closable: bool = True):
        self.setTabsClosable(closable)

    def set_tabs_movable(self, movable: bool = True):
        self.setMovable(movable)

    def _close_tab(self, index: int):
        if not 0 <= index < self.count():
            return False
        widget = self.widget(index)
        self.removeTab(index)
        if widget is not None:
            widget.deleteLater()
        self.tabClosed.emit(index)
        return True


class SegmentedControl(QFrame):
    currentChanged = Signal(int)

    def __init__(self, items: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("SegmentedControl")
        self._buttons: list[QPushButton] = []
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.idClicked.connect(self.currentChanged)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.layout.setSpacing(2)
        for item in items or []:
            self.add_item(item)

    def _reindex(self):
        for button in self._buttons:
            self._group.removeButton(button)
        for index, button in enumerate(self._buttons):
            self._group.addButton(button, index)

    def add_item(self, text: str):
        button = QPushButton(text, self)
        button.setObjectName("SegmentedItem")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        self._buttons.append(button)
        self.layout.addWidget(button)
        self._reindex()
        if len(self._buttons) == 1:
            button.setChecked(True)
        return button

    def remove_item(self, index: int):
        if not 0 <= index < len(self._buttons):
            return None
        previous_index = self.current_index()
        current = self._group.checkedButton()
        button = self._buttons.pop(index)
        was_current = button is current
        self._group.removeButton(button)
        self.layout.removeWidget(button)
        button.deleteLater()
        self._reindex()
        if not self._buttons:
            if previous_index >= 0:
                self.currentChanged.emit(-1)
            return button

        if was_current or current is None:
            current_index = min(index, len(self._buttons) - 1)
        else:
            current_index = self._buttons.index(current)
        self._buttons[current_index].setChecked(True)
        if was_current or current_index != previous_index:
            self.currentChanged.emit(current_index)
        return button

    def clear(self):
        while self._buttons:
            self.remove_item(len(self._buttons) - 1)

    def set_current(self, index: int):
        if not 0 <= index < len(self._buttons):
            return False
        changed = self.current_index() != index
        self._buttons[index].setChecked(True)
        if changed:
            self.currentChanged.emit(index)
        return True

    def current_index(self) -> int:
        return self._group.checkedId()


class BreadcrumbBar(QWidget):
    currentChanged = Signal(int)

    def __init__(self, items: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self._labels: list[str] = list(items or [])
        self._buttons: list[QPushButton] = []
        self._rebuild()

    def _rebuild(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._buttons.clear()
        for index, text in enumerate(self._labels):
            if index:
                separator = CaptionText("/")
                separator.setAccessibleName("层级分隔")
                self.layout.addWidget(separator)
            button = TransparentButton(text)
            button.clicked.connect(
                lambda checked=False, i=index: self.currentChanged.emit(i)
            )
            self._buttons.append(button)
            self.layout.addWidget(button)
        self.layout.addStretch(1)

    def add_item(self, text: str):
        self._labels.append(text)
        self._rebuild()
        return self._buttons[-1]

    def remove_item(self, index: int):
        if not 0 <= index < len(self._labels):
            return None
        text = self._labels.pop(index)
        self._rebuild()
        return text

    def clear(self):
        self._labels.clear()
        self._rebuild()

    def set_current(self, index: int):
        if not 0 <= index < len(self._labels):
            return False
        self.currentChanged.emit(index)
        return True

    def set_items(self, items: list[str]):
        self._labels = list(items)
        self._rebuild()

    def remove_after(self, index: int):
        self._labels = self._labels[: index + 1]
        self._rebuild()


@dataclass
class _CommandItem:
    button: QPushButton
    text: str
    icon: str | IconSpec | QIcon | None
    callback: object


class CommandBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CommandBar")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self._items: list[_CommandItem] = []
        self._overflow_menu = QMenu(self)
        self._overflow_menu.setObjectName("ModernMenu")
        install_window_icon(self._overflow_menu, "menu")
        self._more_button = ToolButton("menu", "更多命令", self)
        self._more_button.clicked.connect(self._show_overflow)
        self._more_button.hide()
        self.layout.addWidget(self._more_button)
        self._overflow_timer = QTimer(self)
        self._overflow_timer.setSingleShot(True)
        self._overflow_timer.timeout.connect(self._update_overflow)
        ThemeManager.instance().themeChanged.connect(self._on_theme_changed)

    def add_action(self, text: str, icon=None, callback=None, primary: bool = False):
        button = PrimaryButton(text, icon) if primary else SecondaryButton(text, icon)
        if callback:
            button.clicked.connect(callback)
        self._items.append(_CommandItem(button, text, icon, callback))
        self.layout.insertWidget(max(0, self.layout.count() - 1), button)
        self._overflow_timer.start(0)
        return button

    def add_spacer(self):
        self.layout.insertStretch(max(0, self.layout.count() - 1), 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_overflow()

    def _update_overflow(self):
        if not self._items:
            self._more_button.hide()
            return

        spacing = max(0, self.layout.spacing())
        total = sum(item.button.sizeHint().width() + spacing for item in self._items)
        if total <= self.width():
            for item in self._items:
                item.button.show()
            self._overflow_menu.clear()
            self._more_button.hide()
            return

        available = max(0, self.width() - self._more_button.sizeHint().width() - spacing)
        used = 0
        hidden = []
        for item in self._items:
            required = item.button.sizeHint().width() + spacing
            visible = used + required <= available
            item.button.setVisible(visible)
            if visible:
                used += required
            else:
                hidden.append(item)
        self._overflow_menu.clear()
        for item in hidden:
            action = QAction(IconResolver.resolve(item.icon), item.text, self._overflow_menu)
            action.setEnabled(item.button.isEnabled())
            action.setCheckable(item.button.isCheckable())
            action.setChecked(item.button.isChecked())
            action.triggered.connect(item.button.click)
            self._overflow_menu.addAction(action)
        self._more_button.setVisible(bool(hidden))

    def _show_overflow(self):
        self._update_overflow()
        if not self._overflow_menu.isEmpty():
            self._overflow_menu.popup(
                self._more_button.mapToGlobal(self._more_button.rect().bottomLeft())
            )

    def _on_theme_changed(self, palette=None):
        self._update_overflow()


class Pagination(QFrame):
    currentChanged = Signal(int)

    def __init__(self, page_count: int = 1, current: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("Pagination")
        self._page_count = max(0, page_count)
        self._current = max(0, min(current, max(0, self._page_count - 1)))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.previous_button = ToolButton("back", "上一页")
        self.next_button = ToolButton("next", "下一页")
        self.label = BodyText()
        self.label.setAlignment(Qt.AlignCenter)
        self.previous_button.clicked.connect(lambda: self.set_current(self._current - 1))
        self.next_button.clicked.connect(lambda: self.set_current(self._current + 1))
        layout.addWidget(self.previous_button)
        layout.addWidget(self.label)
        layout.addWidget(self.next_button)
        self._refresh()

    def _refresh(self):
        shown = self._current + 1 if self._page_count else 0
        self.label.setText(f"{shown} / {self._page_count}")
        self.previous_button.setEnabled(self._current > 0)
        self.next_button.setEnabled(self._current + 1 < self._page_count)

    def set_current(self, index: int):
        if not 0 <= index < self._page_count or index == self._current:
            return False
        self._current = index
        self._refresh()
        self.currentChanged.emit(index)
        return True

    def current_index(self):
        return self._current

    def set_page_count(self, count: int):
        previous = self._current
        self._page_count = max(0, count)
        self._current = min(self._current, max(0, self._page_count - 1))
        self._refresh()
        if self._current != previous:
            self.currentChanged.emit(self._current)

    def add_item(self, text: str = ""):
        self.set_page_count(self._page_count + 1)
        return self._page_count - 1

    def remove_item(self, index: int):
        if not 0 <= index < self._page_count:
            return False
        previous = self._current
        self._page_count -= 1
        if self._page_count == 0:
            self._current = 0
        elif index < self._current:
            self._current -= 1
        else:
            self._current = min(self._current, self._page_count - 1)
        self._refresh()
        if self._current != previous:
            self.currentChanged.emit(self._current)
        return True

    def clear(self):
        self.set_page_count(0)


class CardGrid(QWidget):
    def __init__(
        self,
        columns: int = 3,
        parent=None,
        *,
        minimum_card_width: int = 240,
        adaptive: bool = True,
    ):
        super().__init__(parent)
        self.setObjectName("CardGrid")
        self.columns = max(1, columns)
        self.minimum_card_width = max(120, minimum_card_width)
        self.adaptive = adaptive
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(16)
        self.layout.setVerticalSpacing(16)
        self._cards: list[QWidget] = []
        self._active_columns = self.columns

    def add_card(self, card: QWidget):
        if card in self._cards:
            return card
        self._cards.append(card)
        self._reflow()
        return card

    def remove_card(self, card: QWidget):
        if card not in self._cards:
            return False
        self._cards.remove(card)
        self.layout.removeWidget(card)
        self._reflow()
        return True

    def clear(self):
        for card in list(self._cards):
            self.layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()

    def _reflow(self):
        spacing = self.layout.horizontalSpacing()
        if self.adaptive:
            columns = max(1, min(self.columns, (max(1, self.width()) + spacing) // (self.minimum_card_width + spacing)))
        else:
            columns = self.columns
        self._active_columns = columns
        for index, card in enumerate(self._cards):
            self.layout.addWidget(card, index // columns, index % columns)
        for column in range(self.columns):
            self.layout.setColumnStretch(column, 1 if column < columns else 0)


class ScrollablePanel(QScrollArea):
    def __init__(self, content: QWidget | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ScrollablePanel")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.viewport().setAutoFillBackground(False)
        if content is not None:
            self.setWidget(content)


__all__ = [
    "BreadcrumbBar",
    "CardGrid",
    "CommandBar",
    "DataTable",
    "DataTableView",
    "ModernList",
    "ModernListView",
    "ModernTabs",
    "ModernTree",
    "ModernTreeView",
    "Pagination",
    "ScrollablePanel",
    "SegmentedControl",
]
