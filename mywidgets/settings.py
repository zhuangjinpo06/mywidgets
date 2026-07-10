from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .buttons import (
    HyperlinkButton,
    PrimaryButton,
    RadioButton,
    SecondaryButton,
    ToolButton,
)
from .core import IconResolver, IconSpec, choose_existing_directory
from .inputs import ComboSelect, RangeSlider, ToggleSwitch
from .theme import ThemeManager
from .typography import BodyText, CaptionText, StrongText


class SettingGroup(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingGroup")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 18)
        self.layout.setSpacing(12)
        self.layout.addWidget(StrongText(title))
        self._cards: list[QWidget] = []

    def add_card(self, card: QWidget):
        self._cards.append(card)
        self.layout.addWidget(card)
        return card

    def remove_card(self, card: QWidget):
        if card not in self._cards:
            return False
        self._cards.remove(card)
        self.layout.removeWidget(card)
        card.setParent(None)
        return True

    def clear(self):
        for card in list(self._cards):
            self.remove_card(card)


class SettingCard(QFrame):
    def __init__(
        self,
        title: str,
        content: str = "",
        icon: str | IconSpec | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("SettingCard")
        self.setMinimumHeight(64)
        self._icon_spec = icon
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(14, 12, 14, 12)
        self._outer.setSpacing(10)
        self.root = QHBoxLayout()
        self.root.setSpacing(12)
        self._outer.addLayout(self.root)
        self.icon_label = QLabel(self)
        if icon:
            self.root.addWidget(self.icon_label)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_label = BodyText(title, self)
        text_layout.addWidget(self.title_label)
        self.content_label = CaptionText(content, self)
        self.content_label.setWordWrap(True)
        text_layout.addWidget(self.content_label)
        self.content_label.setVisible(bool(content))
        self.root.addLayout(text_layout, 1)
        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(8)
        self.root.addLayout(self.action_layout)
        ThemeManager.instance().themeChanged.connect(self._refresh_icon)
        self._refresh_icon()

    def _refresh_icon(self, palette=None):
        if self._icon_spec:
            self.icon_label.setPixmap(
                IconResolver.resolve(self._icon_spec, "accent").pixmap(22, 22)
            )

    def add_action_widget(self, widget: QWidget):
        self.action_layout.addWidget(widget)
        return widget


class SwitchSettingCard(SettingCard):
    checkedChanged = Signal(bool)

    def __init__(self, title: str, content: str = "", icon=None, checked: bool = False, parent=None):
        super().__init__(title, content, icon, parent)
        self.switch = ToggleSwitch()
        self.switch.setChecked(checked)
        self.switch.checkedChanged.connect(self.checkedChanged)
        self.add_action_widget(self.switch)


class RangeSettingCard(SettingCard):
    valueChanged = Signal(int)

    def __init__(
        self,
        title: str,
        content: str = "",
        icon=None,
        minimum: int = 0,
        maximum: int = 100,
        value: int = 0,
        parent=None,
    ):
        super().__init__(title, content, icon, parent)
        self.value_label = CaptionText(str(value))
        self.value_label.setMinimumWidth(28)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.slider = RangeSlider(Qt.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setValue(value)
        self.slider.setMinimumWidth(110)
        self.slider.setMaximumWidth(240)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.add_action_widget(self.slider)
        self.add_action_widget(self.value_label)

    def _on_value_changed(self, value: int):
        self.value_label.setText(str(value))
        self.valueChanged.emit(value)


class ComboSettingCard(SettingCard):
    currentTextChanged = Signal(str)

    def __init__(self, title: str, items: list[str], content: str = "", icon=None, parent=None):
        super().__init__(title, content, icon, parent)
        self.combo = ComboSelect(items)
        self.combo.setMinimumWidth(120)
        self.combo.setMaximumWidth(220)
        self.combo.currentTextChanged.connect(self.currentTextChanged)
        self.add_action_widget(self.combo)


class PushSettingCard(SettingCard):
    def __init__(
        self,
        title: str,
        button_text: str,
        content: str = "",
        icon=None,
        primary: bool = False,
        parent=None,
    ):
        super().__init__(title, content, icon, parent)
        self.button = PrimaryButton(button_text) if primary else SecondaryButton(button_text)
        self.add_action_widget(self.button)


class ColorSettingCard(SettingCard):
    colorChanged = Signal(str)

    def __init__(
        self,
        title: str,
        colors: list[str],
        content: str = "",
        icon="palette",
        parent=None,
        *,
        current: str | None = None,
    ):
        super().__init__(title, content, icon, parent)
        self.colors = list(colors)
        self.buttons: list[QPushButton] = []
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for color in self.colors:
            button = QPushButton(self)
            button.setObjectName("ColorSwatch")
            button.setCheckable(True)
            button.setAccessibleName(color)
            button.setToolTip(color)
            button.setFixedSize(28, 28)
            button.clicked.connect(
                lambda checked=False, selected=color: self.colorChanged.emit(selected)
                if checked
                else None
            )
            self.group.addButton(button)
            self.buttons.append(button)
            self.add_action_widget(button)
        if self.buttons:
            self.set_current(current or self.colors[0])
        ThemeManager.instance().themeChanged.connect(self._refresh_swatches)
        self._refresh_swatches()

    def _refresh_swatches(self, palette=None):
        theme = palette or ThemeManager.instance().palette
        for button, color in zip(self.buttons, self.colors):
            button.setStyleSheet(
                f"QPushButton#ColorSwatch {{ background: {color}; border: 2px solid transparent; border-radius: 6px; }}"
                f"QPushButton#ColorSwatch:hover {{ border-color: {theme.muted}; }}"
                f"QPushButton#ColorSwatch:checked {{ border-color: {theme.text}; }}"
            )

    def set_current(self, color: str):
        if color not in self.colors:
            return False
        self.buttons[self.colors.index(color)].setChecked(True)
        return True

    def current(self):
        checked = self.group.checkedButton()
        if checked is None:
            return ""
        return self.colors[self.buttons.index(checked)]


class OptionsSettingCard(SettingCard):
    currentChanged = Signal(str)

    def __init__(
        self,
        title: str,
        options: list[str],
        content: str = "",
        icon=None,
        current: str | None = None,
        parent=None,
    ):
        super().__init__(title, content, icon, parent)
        self.options = list(options)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons: list[RadioButton] = []
        for option in self.options:
            button = RadioButton(option, self)
            button.toggled.connect(
                lambda checked, value=option: self.currentChanged.emit(value) if checked else None
            )
            self.group.addButton(button)
            self.buttons.append(button)
            self.add_action_widget(button)
        if self.buttons:
            self.set_current(current or self.options[0])

    def set_current(self, value: str):
        if value not in self.options:
            return False
        self.buttons[self.options.index(value)].setChecked(True)
        return True

    def current(self):
        checked = self.group.checkedButton()
        return checked.text() if checked else ""


class ExpandSettingCard(SettingCard):
    expandedChanged = Signal(bool)

    def __init__(self, title: str, content: str = "", icon=None, expanded: bool = False, parent=None):
        super().__init__(title, content, icon, parent)
        self.expand_button = ToolButton("chevron_down", "展开")
        self.expand_button.setCheckable(True)
        self.expand_button.toggled.connect(self.set_expanded)
        self.add_action_widget(self.expand_button)
        self.body = QWidget(self)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(34, 4, 0, 0)
        self.body_layout.setSpacing(8)
        self._outer.addWidget(self.body)
        self.set_expanded(expanded)

    def add_widget(self, widget: QWidget):
        self.body_layout.addWidget(widget)
        return widget

    def set_expanded(self, expanded: bool):
        expanded = bool(expanded)
        self.body.setVisible(expanded)
        self.expand_button.blockSignals(True)
        self.expand_button.setChecked(expanded)
        self.expand_button.set_icon("chevron_up" if expanded else "chevron_down")
        self.expand_button.blockSignals(False)
        self.expandedChanged.emit(expanded)


class FolderListSettingCard(ExpandSettingCard):
    pathsChanged = Signal(list)

    def __init__(
        self,
        title: str,
        paths: list[str] | None = None,
        content: str = "",
        icon: str | IconSpec | None = "folder",
        parent=None,
    ):
        super().__init__(title, content, icon, bool(paths), parent)
        self.list_widget = QListWidget(self.body)
        self.list_widget.setObjectName("ModernList")
        self.list_widget.addItems(paths or [])
        self.add_widget(self.list_widget)
        actions = QWidget(self.body)
        action_layout = QHBoxLayout(actions)
        action_layout.setContentsMargins(0, 0, 0, 0)
        self.add_button = SecondaryButton("添加", "add")
        self.remove_button = SecondaryButton("移除", "delete")
        self.add_button.clicked.connect(self.choose_folder)
        self.remove_button.clicked.connect(self.remove_selected)
        action_layout.addWidget(self.add_button)
        action_layout.addWidget(self.remove_button)
        action_layout.addStretch(1)
        self.add_widget(actions)

    def paths(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def add_path(self, path: str):
        if path and path not in self.paths():
            self.list_widget.addItem(path)
            self.pathsChanged.emit(self.paths())
            return True
        return False

    def choose_folder(self):
        path = choose_existing_directory(self, "选择文件夹")
        if path:
            self.add_path(path)

    def remove_selected(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)
            self.pathsChanged.emit(self.paths())


class HyperlinkSettingCard(SettingCard):
    def __init__(
        self,
        title: str,
        link_text: str,
        url: str,
        content: str = "",
        icon=None,
        parent=None,
    ):
        super().__init__(title, content, icon, parent)
        self.link = HyperlinkButton(link_text, url)
        self.add_action_widget(self.link)


__all__ = [
    "ColorSettingCard",
    "ComboSettingCard",
    "ExpandSettingCard",
    "FolderListSettingCard",
    "HyperlinkSettingCard",
    "OptionsSettingCard",
    "PushSettingCard",
    "RangeSettingCard",
    "SettingCard",
    "SettingGroup",
    "SwitchSettingCard",
]
