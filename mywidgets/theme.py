from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path
import re
import sys

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QFontMetrics, QPalette
from PySide6.QtWidgets import QApplication


DEFAULT_ACCENT = "#3f8cff"


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass(frozen=True)
class ThemePalette:
    mode: ThemeMode
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str
    background: str
    surface: str
    surface_alt: str
    nav: str
    border: str
    text: str
    muted: str
    muted_soft: str
    input: str
    table_alt: str
    danger: str
    success: str
    warning: str
    info: str
    shadow: str
    disabled: str
    focus: str
    neutral: str
    on_accent: str = "#ffffff"


class ThemeManager(QObject):
    themeChanged = Signal(object)
    _instance: "ThemeManager | None" = None

    def __init__(self):
        super().__init__()
        self.mode = ThemeMode.LIGHT
        self.accent = DEFAULT_ACCENT
        self.palette = build_palette(self.mode, self.accent)
        self.font_family = ""
        self._auto_app = None
        self._style_hints = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def set_theme(self, app: QApplication, mode: ThemeMode | str | None = None, accent: str | None = None):
        apply_theme(app, mode or self.mode, accent or self.accent)

    def toggle(self, app: QApplication):
        target = ThemeMode.LIGHT if self.palette.mode == ThemeMode.DARK else ThemeMode.DARK
        apply_theme(app, target, self.accent)

    def watch_system_theme(self, app: QApplication):
        if self._auto_app is app:
            return
        self._auto_app = app
        hints = app.styleHints()
        signal = getattr(hints, "colorSchemeChanged", None)
        if signal is not None:
            signal.connect(self._on_system_theme_changed)
            self._style_hints = hints

    def _on_system_theme_changed(self, color_scheme=None):
        if self.mode == ThemeMode.AUTO and self._auto_app is not None:
            apply_theme(self._auto_app, ThemeMode.AUTO, self.accent)


def apply_theme(app: QApplication, mode: ThemeMode | str = ThemeMode.LIGHT, accent: str = DEFAULT_ACCENT):
    if app is None:
        return

    manager = ThemeManager.instance()
    requested_mode = normalize_mode(mode)
    manager.mode = requested_mode
    manager.accent = normalize_color(accent)
    resolved_mode = resolve_mode(app, requested_mode)
    manager.palette = build_palette(resolved_mode, manager.accent)

    font_family = choose_font_family()
    manager.font_family = font_family
    font = QFont(font_family)
    font.setPointSize(10)
    app.setFont(font)
    app.setPalette(build_qpalette(manager.palette))
    app.setStyleSheet(build_stylesheet(manager.palette, font_family))
    if requested_mode == ThemeMode.AUTO:
        manager.watch_system_theme(app)
    manager.themeChanged.emit(manager.palette)


def normalize_mode(mode: ThemeMode | str) -> ThemeMode:
    if isinstance(mode, ThemeMode):
        return mode
    value = str(mode).lower()
    if value == ThemeMode.DARK.value:
        return ThemeMode.DARK
    if value == ThemeMode.AUTO.value:
        return ThemeMode.AUTO
    return ThemeMode.LIGHT


def resolve_mode(app: QApplication, mode: ThemeMode) -> ThemeMode:
    if mode != ThemeMode.AUTO:
        return mode

    hints = app.styleHints()
    color_scheme = getattr(hints, "colorScheme", lambda: None)()
    if color_scheme == Qt.ColorScheme.Dark:
        return ThemeMode.DARK
    if color_scheme == Qt.ColorScheme.Light:
        return ThemeMode.LIGHT

    color = app.palette().color(QPalette.Window)
    return ThemeMode.DARK if color.lightness() < 128 else ThemeMode.LIGHT


def normalize_color(color: str) -> str:
    value = QColor(color)
    return value.name() if value.isValid() else DEFAULT_ACCENT


_RGBA_PATTERN = re.compile(
    r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)",
    re.IGNORECASE,
)


def theme_qcolor(value: str, fallback: str = "#000000") -> QColor:
    """Convert theme CSS colors, including rgba(), into a valid QColor."""
    color = QColor(value)
    if color.isValid():
        return color
    match = _RGBA_PATTERN.fullmatch(str(value))
    if match:
        red, green, blue = (max(0, min(255, int(part))) for part in match.group(1, 2, 3))
        alpha_text = match.group(4)
        if alpha_text is None:
            alpha = 255
        else:
            alpha_value = float(alpha_text)
            alpha = round(alpha_value * 255) if alpha_value <= 1 else round(alpha_value)
        return QColor(red, green, blue, max(0, min(255, alpha)))
    fallback_color = QColor(fallback)
    return fallback_color if fallback_color.isValid() else QColor("#000000")


_FONT_FAMILY_CACHE: str | None = None
_REGISTERED_FONT_PATHS: set[str] = set()


def _supports_cjk(family: str) -> bool:
    if not family:
        return False
    metrics = QFontMetrics(QFont(family, 10))
    return all(metrics.inFontUcs4(ord(character)) for character in "中文控件")


def _system_font_candidates() -> list[Path]:
    paths: list[Path] = []
    if sys.platform.startswith("win"):
        windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
        font_dirs = [windows / "Fonts", windows / "Boot" / "Fonts"]
        names = [
            "msyh.ttc",
            "msyhl.ttc",
            "NotoSansSC-VF.ttf",
            "Deng.ttf",
            "simhei.ttf",
            "simsun.ttc",
            "chs_boot.ttf",
        ]
        paths.extend(directory / name for directory in font_dirs for name in names)
    elif sys.platform == "darwin":
        paths.extend(
            Path(path)
            for path in [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/Library/Fonts/NotoSansCJK-Regular.ttc",
            ]
        )
    else:
        paths.extend(
            Path(path)
            for path in [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/local/share/fonts/NotoSansCJK-Regular.ttc",
            ]
        )
    return paths


def register_system_cjk_fonts() -> list[str]:
    registered: list[str] = []
    for path in _system_font_candidates():
        resolved = str(path)
        if not path.is_file() or resolved in _REGISTERED_FONT_PATHS:
            continue
        font_id = QFontDatabase.addApplicationFont(resolved)
        _REGISTERED_FONT_PATHS.add(resolved)
        if font_id >= 0:
            registered.extend(QFontDatabase.applicationFontFamilies(font_id))
            if any(_supports_cjk(family) for family in registered):
                break
    return registered


def choose_font_family() -> str:
    global _FONT_FAMILY_CACHE
    if _FONT_FAMILY_CACHE and _supports_cjk(_FONT_FAMILY_CACHE):
        return _FONT_FAMILY_CACHE

    candidates = [
        "Microsoft YaHei UI",
        "Microsoft YaHei",
        "PingFang SC",
        "Noto Sans SC",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "DengXian",
        "SimHei",
        "Segoe UI",
    ]
    families = set(QFontDatabase.families())
    for family in candidates:
        if family in families and _supports_cjk(family):
            _FONT_FAMILY_CACHE = family
            return family

    registered = register_system_cjk_fonts()
    families.update(registered)
    families.update(QFontDatabase.families())
    for family in candidates:
        if family in families and _supports_cjk(family):
            _FONT_FAMILY_CACHE = family
            return family
    for family in registered:
        if _supports_cjk(family):
            _FONT_FAMILY_CACHE = family
            return family

    app = QApplication.instance()
    return app.font().family() if app else "Segoe UI"


def build_palette(mode: ThemeMode, accent: str) -> ThemePalette:
    color = QColor(accent)
    hover = color.lighter(112).name()
    pressed = color.darker(112).name()
    r, g, b, _ = color.getRgb()
    accent_soft = f"rgba({r}, {g}, {b}, 33)"

    if mode == ThemeMode.DARK:
        return ThemePalette(
            mode=mode,
            accent=accent,
            accent_hover=hover,
            accent_pressed=pressed,
            accent_soft=accent_soft,
            background="#111418",
            surface="#181c22",
            surface_alt="#20262e",
            nav="#15191f",
            border="#303844",
            text="#f4f7fb",
            muted="#a7b0bd",
            muted_soft="#737d8b",
            input="#151a20",
            table_alt="#1d232b",
            danger="#ff6b6b",
            success="#40c785",
            warning="#fdb022",
            info="#60a5fa",
            shadow="rgba(0, 0, 0, 0.32)",
            disabled="#596270",
            focus="#84b5ff",
            neutral="#a7b0bd",
        )

    return ThemePalette(
        mode=mode,
        accent=accent,
        accent_hover=hover,
        accent_pressed=pressed,
        accent_soft=accent_soft,
        background="#f4f7fb",
        surface="#ffffff",
        surface_alt="#eef3f8",
        nav="#fbfcfe",
        border="#dbe3ee",
        text="#1f2630",
        muted="#667085",
        muted_soft="#8b96a8",
        input="#ffffff",
        table_alt="#f7f9fc",
        danger="#d92d20",
        success="#079455",
        warning="#dc6803",
        info="#2563eb",
        shadow="rgba(15, 23, 42, 0.10)",
        disabled="#a8b2c1",
        focus="#1d6fe8",
        neutral="#667085",
    )


def build_qpalette(palette: ThemePalette) -> QPalette:
    qpalette = QPalette()
    qpalette.setColor(QPalette.Window, QColor(palette.background))
    qpalette.setColor(QPalette.Base, QColor(palette.surface))
    qpalette.setColor(QPalette.AlternateBase, QColor(palette.surface_alt))
    qpalette.setColor(QPalette.Text, QColor(palette.text))
    qpalette.setColor(QPalette.WindowText, QColor(palette.text))
    qpalette.setColor(QPalette.Button, QColor(palette.surface))
    qpalette.setColor(QPalette.ButtonText, QColor(palette.text))
    qpalette.setColor(QPalette.Highlight, QColor(palette.accent))
    qpalette.setColor(QPalette.HighlightedText, QColor(palette.on_accent))
    qpalette.setColor(QPalette.Disabled, QPalette.Text, QColor(palette.disabled))
    qpalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(palette.disabled))
    return qpalette


def build_stylesheet(p: ThemePalette, font_family: str) -> str:
    def soft(color: str, alpha: int = 32) -> str:
        qcolor = QColor(color)
        r, g, b, _ = qcolor.getRgb()
        return f"rgba({r}, {g}, {b}, {alpha})"

    success_soft = soft(p.success)
    warning_soft = soft(p.warning)
    danger_soft = soft(p.danger)
    info_soft = soft(p.info)

    return f"""
    QWidget {{
        background: transparent;
        color: {p.text};
        font-family: "{font_family}", "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: 10pt;
        outline: none;
    }}

    QMainWindow#ModernWindow, QWidget#AppRoot {{
        background: {p.background};
    }}

    QWidget#SideNavigation {{
        background: {p.nav};
        border-right: 1px solid {p.border};
    }}

    QScrollArea#ScrollablePanel {{
        background: transparent;
        border: none;
    }}

    QFrame#CommandBar, QFrame#CardGrid {{
        background: transparent;
        border: none;
    }}

    QLabel[role="brand"] {{
        color: {p.text};
        font-size: 14pt;
        font-weight: 700;
    }}

    QLabel[role="pageTitle"] {{
        color: {p.text};
        font-size: 20pt;
        font-weight: 700;
    }}

    QLabel[role="title"] {{
        color: {p.text};
        font-size: 13pt;
        font-weight: 700;
    }}

    QLabel[role="strong"] {{
        color: {p.text};
        font-weight: 700;
    }}

    QLabel[role="body"] {{
        color: {p.text};
    }}

    QLabel[role="caption"], QLabel[role="muted"] {{
        color: {p.muted};
        font-size: 9pt;
    }}

    QLabel#InfoBadge {{
        min-width: 18px;
        min-height: 18px;
        padding: 1px 6px;
        border-radius: 9px;
        background: {p.accent};
        color: {p.on_accent};
        font-size: 8pt;
        font-weight: 700;
    }}

    QLabel#StatusBadge {{
        min-height: 20px;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 8pt;
        font-weight: 700;
    }}

    QLabel#StatusBadge[kind="success"] {{
        background: {success_soft};
        color: {p.success};
    }}

    QLabel#StatusBadge[kind="warning"] {{
        background: {warning_soft};
        color: {p.warning};
    }}

    QLabel#StatusBadge[kind="error"] {{
        background: {danger_soft};
        color: {p.danger};
    }}

    QLabel#StatusBadge[kind="info"] {{
        background: {info_soft};
        color: {p.info};
    }}

    QPushButton#NavItem {{
        border: none;
        border-radius: 8px;
        padding: 10px 12px;
        color: {p.muted};
        background: transparent;
        text-align: left;
        font-weight: 500;
    }}

    QPushButton#NavItem:hover {{
        color: {p.text};
        background: {p.surface_alt};
    }}

    QPushButton#NavItem:checked {{
        color: {p.accent};
        background: {p.accent_soft};
        font-weight: 700;
    }}

    QPushButton#NavItem[compact="true"] {{
        padding: 10px;
        text-align: center;
    }}

    QFrame#Card, QFrame#Panel {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    QPushButton#PrimaryButton {{
        min-height: 34px;
        padding: 0 16px;
        border: 1px solid {p.accent};
        border-radius: 8px;
        background: {p.accent};
        color: {p.on_accent};
        font-weight: 700;
    }}

    QPushButton#PrimaryButton:hover {{
        background: {p.accent_hover};
        border-color: {p.accent_hover};
    }}

    QPushButton#PrimaryButton:pressed {{
        background: {p.accent_pressed};
        border-color: {p.accent_pressed};
    }}

    QPushButton#PrimaryButton:disabled,
    QPushButton#SecondaryButton:disabled,
    QPushButton#ToggleButton:disabled,
    QPushButton#TransparentButton:disabled,
    QPushButton#DropDownButton:disabled,
    QPushButton#PrimaryDropDownButton:disabled,
    QPushButton#SplitButtonAction:disabled,
    QPushButton#SplitButtonMenu:disabled,
    QPushButton#PrimarySplitButtonAction:disabled,
    QPushButton#PrimarySplitButtonMenu:disabled {{
        color: {p.muted_soft};
        background: {p.surface_alt};
        border-color: {p.border};
    }}

    QPushButton#SecondaryButton, QPushButton#ToggleButton {{
        min-height: 34px;
        padding: 0 14px;
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.surface};
        color: {p.text};
        font-weight: 600;
    }}

    QPushButton#SecondaryButton:hover, QPushButton#ToggleButton:hover {{
        background: {p.surface_alt};
    }}

    QPushButton#ToggleButton:checked {{
        background: {p.accent_soft};
        border-color: {p.accent};
        color: {p.accent};
    }}

    QPushButton#TransparentButton {{
        min-height: 34px;
        padding: 0 12px;
        border: none;
        border-radius: 8px;
        background: transparent;
        color: {p.text};
        font-weight: 600;
    }}

    QPushButton#TransparentButton:hover {{
        background: {p.surface_alt};
    }}

    QFrame#SplitButton {{
        background: transparent;
        border: none;
    }}

    QPushButton#HyperlinkButton {{
        min-height: 30px;
        padding: 0;
        border: none;
        background: transparent;
        color: {p.accent};
        text-align: left;
    }}

    QPushButton#IconButton, QPushButton#ToolButton, QPushButton#MetricIcon {{
        min-width: 36px;
        min-height: 36px;
        max-width: 36px;
        max-height: 36px;
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.surface};
        color: {p.text};
    }}

    QPushButton#MetricIcon {{
        background: {p.accent_soft};
        color: {p.accent};
    }}

    QPushButton#IconButton:hover, QPushButton#ToolButton:hover {{
        background: {p.surface_alt};
    }}

    QLineEdit#TextInput, QLineEdit#SearchInput, QTextEdit#TextArea, QComboBox#ComboSelect {{
        min-height: 34px;
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.input};
        color: {p.text};
        padding: 6px 10px;
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
    }}

    QSpinBox#NumberInput, QDoubleSpinBox#DoubleNumberInput,
    QDateEdit#DatePicker, QDateEdit#CalendarPicker, QDateEdit#MonthPicker,
    QTimeEdit#TimePicker, QTimeEdit#AmPmTimePicker,
    QDateTimeEdit#DateTimePicker {{
        min-height: 34px;
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.input};
        color: {p.text};
        padding: 4px 10px;
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
    }}

    QCheckBox#CheckBox, QRadioButton#RadioButton {{
        min-height: 28px;
        color: {p.text};
        spacing: 8px;
    }}

    QListWidget#ModernList, QTreeWidget#ModernTree {{
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.surface};
        alternate-background-color: {p.table_alt};
        color: {p.text};
        selection-background-color: {p.accent_soft};
        selection-color: {p.text};
    }}

    QListWidget#ModernList::item, QTreeWidget#ModernTree::item {{
        min-height: 32px;
        padding: 4px 8px;
        border-radius: 6px;
    }}

    QListWidget#ModernList::item:hover, QTreeWidget#ModernTree::item:hover {{
        background: {p.surface_alt};
    }}

    QLineEdit#TextInput:focus, QLineEdit#SearchInput:focus, QTextEdit#TextArea:focus, QComboBox#ComboSelect:focus {{
        border-color: {p.accent};
    }}

    QTextEdit#TextArea {{
        min-height: 100px;
    }}

    QComboBox#ComboSelect::drop-down {{
        border: none;
        width: 28px;
    }}

    QComboBox#ComboSelect QAbstractItemView {{
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.surface};
        color: {p.text};
        selection-background-color: {p.accent_soft};
        selection-color: {p.text};
        padding: 4px;
    }}

    QTableWidget#DataTable {{
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.surface};
        alternate-background-color: {p.table_alt};
        color: {p.text};
        gridline-color: {p.border};
        selection-background-color: {p.accent_soft};
        selection-color: {p.text};
    }}

    QHeaderView::section {{
        background: {p.surface};
        color: {p.muted};
        border: none;
        border-bottom: 1px solid {p.border};
        padding: 8px;
        font-weight: 700;
    }}

    QProgressBar#ProgressLine {{
        height: 6px;
        border: none;
        border-radius: 3px;
        background: {p.surface_alt};
        text-align: center;
    }}

    QProgressBar#ProgressLine::chunk {{
        border-radius: 3px;
        background: {p.accent};
    }}

    QSlider#RangeSlider::groove:horizontal {{
        height: 6px;
        border-radius: 3px;
        background: {p.surface_alt};
    }}

    QSlider#RangeSlider::sub-page:horizontal {{
        border-radius: 3px;
        background: {p.accent};
    }}

    QSlider#RangeSlider::handle:horizontal {{
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
        background: {p.surface};
        border: 2px solid {p.accent};
    }}

    QTabWidget#ModernTabs::pane {{
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.surface};
        top: -1px;
    }}

    QTabBar::tab {{
        min-height: 32px;
        padding: 6px 14px;
        border: 1px solid transparent;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        color: {p.muted};
        background: transparent;
    }}

    QTabBar::tab:selected {{
        color: {p.accent};
        background: {p.surface};
        border-color: {p.border};
        font-weight: 700;
    }}

    QFrame#SegmentedControl {{
        background: {p.surface_alt};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    QPushButton#SegmentedItem {{
        min-height: 30px;
        padding: 0 12px;
        border: none;
        border-radius: 6px;
        background: transparent;
        color: {p.muted};
        font-weight: 600;
    }}

    QPushButton#SegmentedItem:checked {{
        background: {p.surface};
        color: {p.accent};
    }}

    QFrame#SettingGroup, QFrame#SettingCard, QFrame#Flyout, QDialog#ModernDialog, QFrame#TeachingTip {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    QFrame#SettingCard:hover {{
        background: {p.table_alt};
    }}

    QMenu#ModernMenu {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: 8px;
        padding: 6px;
    }}

    QMenu#ModernMenu::item {{
        min-height: 28px;
        padding: 6px 28px 6px 12px;
        border-radius: 6px;
        color: {p.text};
    }}

    QMenu#ModernMenu::item:selected {{
        background: {p.surface_alt};
    }}

    QScrollBar:vertical {{
        width: 10px;
        background: transparent;
    }}

    QScrollBar::handle:vertical {{
        min-height: 40px;
        border-radius: 5px;
        background: {p.border};
    }}

    QFrame#Toast {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-left: 4px solid {p.accent};
        border-radius: 8px;
    }}

    QLabel[role="subtitle"] {{
        color: {p.text};
        font-size: 14pt;
        font-weight: 600;
    }}

    QLabel[role="largeTitle"] {{
        color: {p.text};
        font-size: 24pt;
        font-weight: 700;
    }}

    QLabel[role="display"] {{
        color: {p.text};
        font-size: 28pt;
        font-weight: 700;
    }}

    QLabel[role="hyperlink"] {{
        color: {p.accent};
    }}

    QLabel[role="hyperlink"]:hover {{
        color: {p.accent_hover};
        text-decoration: underline;
    }}

    QPushButton:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
    QFrame#ClickableCard:focus, QFrame#ElevatedCard:focus {{
        border-color: {p.focus};
    }}

    QPushButton#PrimaryToolButton {{
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
        border: 1px solid {p.accent};
        border-radius: 8px;
        background: {p.accent};
        color: {p.on_accent};
    }}

    QPushButton#PrimaryToolButton:hover {{ background: {p.accent_hover}; }}

    QPushButton#TransparentToolButton, QPushButton#ToggleToolButton {{
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
    }}

    QPushButton#TransparentToolButton:hover, QPushButton#ToggleToolButton:hover {{
        background: {p.surface_alt};
    }}

    QPushButton#ToggleToolButton:checked {{
        background: {p.accent_soft};
        border-color: {p.accent};
    }}

    QPushButton#DropDownButton, QPushButton#PrimaryDropDownButton {{
        min-height: 34px;
        padding: 0 14px;
        border-radius: 8px;
        font-weight: 600;
    }}

    QPushButton#DropDownButton {{
        color: {p.text};
        background: {p.surface};
        border: 1px solid {p.border};
    }}

    QPushButton#PrimaryDropDownButton {{
        color: {p.on_accent};
        background: {p.accent};
        border: 1px solid {p.accent};
    }}

    QPushButton#DropDownButton:hover {{ background: {p.surface_alt}; }}
    QPushButton#PrimaryDropDownButton:hover {{ background: {p.accent_hover}; }}

    QPushButton#SplitButtonAction, QPushButton#PrimarySplitButtonAction {{
        min-height: 34px;
        padding: 0 14px;
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
        font-weight: 600;
    }}

    QPushButton#SplitButtonMenu, QPushButton#PrimarySplitButtonMenu {{
        min-width: 36px;
        max-width: 36px;
        min-height: 34px;
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }}

    QPushButton#SplitButtonAction, QPushButton#SplitButtonMenu {{
        color: {p.text};
        background: {p.surface};
        border: 1px solid {p.border};
    }}

    QPushButton#SplitButtonAction {{ border-right: none; }}

    QPushButton#PrimarySplitButtonAction, QPushButton#PrimarySplitButtonMenu {{
        color: {p.on_accent};
        background: {p.accent};
        border: 1px solid {p.accent};
    }}

    QPushButton#PrimarySplitButtonAction {{ border-right: none; }}

    QPushButton#PillButton {{
        min-height: 34px;
        padding: 0 16px;
        border: 1px solid {p.border};
        border-radius: 17px;
        color: {p.text};
        background: {p.surface};
    }}

    QPushButton#PillButton:checked {{
        color: {p.accent};
        border-color: {p.accent};
        background: {p.accent_soft};
    }}

    QLineEdit#TextInput, QLineEdit#SearchInput, QTextEdit#TextArea,
    QPlainTextEdit#PlainTextArea, QComboBox#ComboSelect,
    QSpinBox#NumberInput, QDoubleSpinBox#DoubleNumberInput {{
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.input};
        color: {p.text};
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
    }}

    QPlainTextEdit#PlainTextArea {{ min-height: 100px; padding: 6px 10px; }}

    QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
        subcontrol-origin: border;
        width: 24px;
        border: none;
        background: transparent;
    }}

    QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{
        background: {p.surface_alt};
    }}

    QDateEdit#DatePicker::drop-down, QDateEdit#CalendarPicker::drop-down,
    QDateTimeEdit#DateTimePicker::drop-down {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 28px;
        border: none;
        background: transparent;
    }}

    QDateEdit#DatePicker::drop-down:hover, QDateEdit#CalendarPicker::drop-down:hover,
    QDateTimeEdit#DateTimePicker::drop-down:hover {{
        background: {p.surface_alt};
    }}

    QCalendarWidget#FluentCalendar {{
        background: {p.surface};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    QCalendarWidget#FluentCalendar QWidget#qt_calendar_navigationbar {{
        background: {p.surface_alt};
        border: none;
        border-bottom: 1px solid {p.border};
    }}

    QCalendarWidget#FluentCalendar QToolButton {{
        min-width: 30px;
        min-height: 30px;
        padding: 2px 8px;
        border: none;
        border-radius: 6px;
        background: transparent;
        color: {p.text};
        font-weight: 600;
        icon-size: 14px;
    }}

    QCalendarWidget#FluentCalendar QToolButton:hover {{
        background: {p.accent_soft};
        color: {p.accent};
    }}

    QCalendarWidget#FluentCalendar QSpinBox#qt_calendar_yearedit {{
        min-height: 28px;
        padding: 0 6px;
        border: 1px solid {p.accent};
        border-radius: 6px;
        background: {p.input};
        color: {p.text};
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
    }}

    QCalendarWidget#FluentCalendar QAbstractItemView {{
        background: {p.surface};
        alternate-background-color: {p.surface};
        color: {p.text};
        border: none;
        gridline-color: {p.border};
        selection-background-color: {p.accent};
        selection-color: {p.on_accent};
        outline: none;
    }}

    QCalendarWidget#FluentCalendar QAbstractItemView:item:hover {{
        background: {p.accent_soft};
        color: {p.text};
    }}

    QCalendarWidget#FluentCalendar QAbstractItemView:item:selected {{
        background: {p.accent};
        color: {p.on_accent};
    }}

    QFrame#ClickableCard, QFrame#ElevatedCard, QFrame#HeaderCard {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    QFrame#ClickableCard:hover, QFrame#ElevatedCard:hover {{
        border-color: {p.accent};
        background: {p.table_alt};
    }}

    QFrame#HeaderCardHeader {{
        background: {p.surface_alt};
        border: none;
        border-bottom: 1px solid {p.border};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}

    QLabel#StatusBadge {{
        min-height: 20px;
        padding: 1px 8px;
        border-radius: 10px;
        font-size: 8pt;
        font-weight: 600;
    }}

    QLabel#StatusBadge[kind="neutral"] {{ color: {p.neutral}; background: {soft(p.neutral)}; }}
    QLabel#StatusBadge[kind="info"] {{ color: {p.info}; background: {info_soft}; }}
    QLabel#StatusBadge[kind="success"] {{ color: {p.success}; background: {success_soft}; }}
    QLabel#StatusBadge[kind="warning"] {{ color: {p.warning}; background: {warning_soft}; }}
    QLabel#StatusBadge[kind="error"] {{ color: {p.danger}; background: {danger_soft}; }}

    QLabel#DotBadge {{ min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px; padding: 0; border-radius: 5px; }}
    QLabel#DotBadge[kind="neutral"] {{ background: {p.neutral}; }}
    QLabel#DotBadge[kind="info"] {{ background: {p.info}; }}
    QLabel#DotBadge[kind="success"] {{ background: {p.success}; }}
    QLabel#DotBadge[kind="warning"] {{ background: {p.warning}; }}
    QLabel#DotBadge[kind="error"] {{ background: {p.danger}; }}

    QFrame#HorizontalSeparator, QFrame#VerticalSeparator,
    QFrame#NavigationSeparator {{ background: {p.border}; border: none; }}

    QLabel#ImageView {{
        background: {p.surface_alt};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    QListView#ModernListView, QTreeView#ModernTreeView, QTableView#DataTableView {{
        border: 1px solid {p.border};
        border-radius: 8px;
        background: {p.surface};
        alternate-background-color: {p.table_alt};
        selection-background-color: {p.accent_soft};
        selection-color: {p.text};
    }}

    QFrame#Pagination {{ background: transparent; border: none; }}

    QFrame#PivotControl {{
        background: transparent;
        border: none;
    }}

    QProgressBar#IndeterminateProgressLine {{
        min-height: 5px;
        max-height: 5px;
        border: none;
        border-radius: 2px;
        background: {p.surface_alt};
    }}

    QProgressBar#IndeterminateProgressLine::chunk {{
        background: {p.accent};
        border-radius: 2px;
    }}

    QFrame#InfoBanner, QFrame#StateTooltip {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    QFrame#StateTooltip[kind="success"] {{ border-left: 4px solid {p.success}; }}
    QFrame#StateTooltip[kind="error"] {{ border-left: 4px solid {p.danger}; }}

    QFrame#InfoBanner[kind="info"] {{ border-left: 4px solid {p.info}; }}
    QFrame#InfoBanner[kind="success"] {{ border-left: 4px solid {p.success}; }}
    QFrame#InfoBanner[kind="warning"] {{ border-left: 4px solid {p.warning}; }}
    QFrame#InfoBanner[kind="error"] {{ border-left: 4px solid {p.danger}; }}

    QFrame#Toast[kind="info"] {{ border-left-color: {p.info}; }}
    QFrame#Toast[kind="success"] {{ border-left-color: {p.success}; }}
    QFrame#Toast[kind="warning"] {{ border-left-color: {p.warning}; }}
    QFrame#Toast[kind="error"] {{ border-left-color: {p.danger}; }}

    QLabel#NavigationHeader {{ color: {p.muted}; font-size: 8pt; font-weight: 600; }}

    QWidget#SplashScreen {{ background: {p.background}; }}

    QWidget:disabled {{ color: {p.disabled}; }}
    """


class ConfigStore:
    """Tiny JSON-backed settings helper for mywidgets demos and small tools."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: dict[str, object] = {}
        self.load()

    def load(self):
        if not self.path.exists():
            self.data = {}
            return self.data

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            self.data = loaded if isinstance(loaded, dict) else {}
        except (OSError, json.JSONDecodeError):
            self.data = {}
        return self.data

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
        return self.path

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value, save: bool = True):
        self.data[key] = value
        if save:
            self.save()

    def update(self, values: dict[str, object], save: bool = True):
        self.data.update(values)
        if save:
            self.save()

    def delete(self, key: str, save: bool = True):
        existed = key in self.data
        self.data.pop(key, None)
        if existed and save:
            self.save()
        return existed

    def clear(self, save: bool = True):
        changed = bool(self.data)
        self.data.clear()
        if changed and save:
            self.save()
        return changed
