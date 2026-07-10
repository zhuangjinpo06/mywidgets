from __future__ import annotations

from PySide6.QtCore import QDate, QDateTime, QTime, Qt
from PySide6.QtGui import QPalette, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
    QDateTimeEdit,
    QTimeEdit,
    QToolButton,
)

from .control_style import install_arrow_overlay
from .core import IconResolver
from .theme import ThemeManager, theme_qcolor


class _DateTimeThemeSupport:
    def _init_date_time_theme(self, has_calendar: bool = False):
        install_arrow_overlay(self, "dropdown" if has_calendar else "spin")
        self._fluent_calendar = None
        if has_calendar:
            self.setCalendarPopup(True)
            self._fluent_calendar = self.calendarWidget()
            self._fluent_calendar.setObjectName("FluentCalendar")
            self._fluent_calendar.setGridVisible(False)
            self._fluent_calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
            self._fluent_calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        ThemeManager.instance().themeChanged.connect(self._refresh_date_time_theme)
        self._refresh_date_time_theme()

    def _refresh_date_time_theme(self, palette=None):
        theme = palette or ThemeManager.instance().palette
        self.update()
        if self.lineEdit() is not None:
            self.lineEdit().update()
        calendar = self._fluent_calendar
        if calendar is None:
            return

        calendar_palette = calendar.palette()
        calendar_palette.setColor(QPalette.Window, theme_qcolor(theme.surface))
        calendar_palette.setColor(QPalette.Base, theme_qcolor(theme.surface))
        calendar_palette.setColor(QPalette.AlternateBase, theme_qcolor(theme.surface_alt))
        calendar_palette.setColor(QPalette.Text, theme_qcolor(theme.text))
        calendar_palette.setColor(QPalette.WindowText, theme_qcolor(theme.text))
        calendar_palette.setColor(QPalette.ButtonText, theme_qcolor(theme.text))
        calendar_palette.setColor(QPalette.Highlight, theme_qcolor(theme.accent))
        calendar_palette.setColor(QPalette.HighlightedText, theme_qcolor(theme.on_accent))
        calendar_palette.setColor(QPalette.Disabled, QPalette.Text, theme_qcolor(theme.disabled))
        header_format = QTextCharFormat()
        header_format.setForeground(theme_qcolor(theme.muted))
        calendar.setHeaderTextFormat(header_format)
        weekday_format = QTextCharFormat()
        weekday_format.setForeground(theme_qcolor(theme.text))
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(theme_qcolor(theme.danger))
        for day in (
            Qt.Monday,
            Qt.Tuesday,
            Qt.Wednesday,
            Qt.Thursday,
            Qt.Friday,
        ):
            calendar.setWeekdayTextFormat(day, weekday_format)
        calendar.setWeekdayTextFormat(Qt.Saturday, weekend_format)
        calendar.setWeekdayTextFormat(Qt.Sunday, weekend_format)

        previous = calendar.findChild(QToolButton, "qt_calendar_prevmonth")
        next_button = calendar.findChild(QToolButton, "qt_calendar_nextmonth")
        if previous is not None:
            previous.setIcon(IconResolver.resolve("back", "text"))
            previous.setToolTip("上个月")
        if next_button is not None:
            next_button.setIcon(IconResolver.resolve("next", "text"))
            next_button.setToolTip("下个月")
        calendar.style().unpolish(calendar)
        calendar.style().polish(calendar)
        calendar.setPalette(calendar_palette)
        calendar.update()


class DatePicker(_DateTimeThemeSupport, QDateEdit):
    def __init__(self, parent=None):
        QDateEdit.__init__(self, parent)
        self.setObjectName("DatePicker")
        self.setDisplayFormat("yyyy-MM-dd")
        self.setDate(QDate.currentDate())
        self._init_date_time_theme(True)


class TimePicker(_DateTimeThemeSupport, QTimeEdit):
    def __init__(self, parent=None):
        QTimeEdit.__init__(self, parent)
        self.setObjectName("TimePicker")
        self.setDisplayFormat("HH:mm:ss")
        self.setTime(QTime.currentTime())
        self._init_date_time_theme(False)


class DateTimePicker(_DateTimeThemeSupport, QDateTimeEdit):
    def __init__(self, parent=None):
        QDateTimeEdit.__init__(self, parent)
        self.setObjectName("DateTimePicker")
        self.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.setDateTime(QDateTime.currentDateTime())
        self._init_date_time_theme(True)


class CalendarPicker(DatePicker):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CalendarPicker")


class MonthPicker(_DateTimeThemeSupport, QDateEdit):
    def __init__(self, parent=None):
        QDateEdit.__init__(self, parent)
        self.setObjectName("MonthPicker")
        self.setDisplayFormat("yyyy-MM")
        self.setCalendarPopup(False)
        current = QDate.currentDate()
        self.setDate(QDate(current.year(), current.month(), 1))
        self._init_date_time_theme(False)

    def setDate(self, date: QDate):
        if date.isValid():
            date = QDate(date.year(), date.month(), 1)
        QDateEdit.setDate(self, date)


class AmPmTimePicker(_DateTimeThemeSupport, QTimeEdit):
    def __init__(self, parent=None):
        QTimeEdit.__init__(self, parent)
        self.setObjectName("AmPmTimePicker")
        self.setDisplayFormat("hh:mm AP")
        self.setTime(QTime.currentTime())
        self._init_date_time_theme(False)


__all__ = [
    "AmPmTimePicker",
    "CalendarPicker",
    "DatePicker",
    "DateTimePicker",
    "MonthPicker",
    "TimePicker",
]
