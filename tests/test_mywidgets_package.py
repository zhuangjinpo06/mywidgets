import importlib
import os
import pkgutil
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QDate, QEvent, QPoint, QRect, QTime, Qt
from PySide6.QtGui import QAction, QColor, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton, QWidget

import mywidgets
from examples.gallery import GalleryWindow
from mywidgets.core import create_existing_directory_dialog
from mywidgets.resource import ICON_ALIASES, WINDOW_ICON_ALIASES
from tests._qt import get_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = get_app()
        mywidgets.apply_theme(cls.app, mywidgets.ThemeMode.LIGHT, "#3f8cff")

    def tearDown(self):
        mywidgets.ToastManager.close_all()
        self.app.processEvents()
        mywidgets.apply_theme(self.app, mywidgets.ThemeMode.LIGHT, "#3f8cff")

    def test_all_modules_import(self):
        modules = [
            info.name
            for info in pkgutil.iter_modules(mywidgets.__path__, mywidgets.__name__ + ".")
        ]
        for module in modules:
            importlib.import_module(module)
        self.assertIn("mywidgets.resource", modules)
        self.assertGreaterEqual(len(modules), 18)

    def test_public_exports_and_version(self):
        self.assertEqual("0.1.1", mywidgets.__version__)
        self.assertEqual(len(mywidgets.__all__), len(set(mywidgets.__all__)))
        self.assertGreaterEqual(len(mywidgets.__all__), 120)
        for name in (
            "ModernWindow",
            "DatePicker",
            "ToastManager",
            "FolderListDialog",
            "ConfigStore",
        ):
            self.assertTrue(hasattr(mywidgets, name), name)

    def test_compatibility_facades_import(self):
        from mywidgets.controls import PrimaryButton as ControlsButton
        from mywidgets.widgets import PrimaryButton as WidgetsButton

        self.assertIs(mywidgets.PrimaryButton, ControlsButton)
        self.assertIs(mywidgets.PrimaryButton, WidgetsButton)

    def test_icon_resources_resolve(self):
        self.assertGreaterEqual(len(ICON_ALIASES), 90)
        unresolved = [
            name for name in ICON_ALIASES if mywidgets.IconResolver.resolve(name).isNull()
        ]
        self.assertEqual([], unresolved)
        self.assertIn("folder", WINDOW_ICON_ALIASES)

    def test_windows_and_popups_have_icons(self):
        widgets = [
            mywidgets.ModernWindow(),
            mywidgets.ModernMenu(),
            mywidgets.CheckableMenu("Env"),
            mywidgets.MessageBox("Confirm", "Continue?"),
            mywidgets.ColorDialog(),
            mywidgets.FolderListDialog(),
            mywidgets.SplashScreen(),
            mywidgets.StateTooltip("Loading"),
            create_existing_directory_dialog(),
        ]
        for widget in widgets:
            self.assertFalse(widget.windowIcon().isNull(), type(widget).__name__)
        menu = mywidgets.ModernMenu()
        before = menu.windowIcon().cacheKey()
        mywidgets.apply_theme(self.app, mywidgets.ThemeMode.DARK, "#00a389")
        self.app.processEvents()
        self.assertNotEqual(menu.windowIcon().cacheKey(), before)
        widgets.append(menu)
        for widget in widgets:
            widget.close()

    def test_core_widgets_construct_and_theme_switch(self):
        menu = mywidgets.ModernMenu()
        factories = [
            lambda: mywidgets.PrimaryButton("Primary", "send"),
            lambda: mywidgets.SecondaryButton("Secondary", "save"),
            lambda: mywidgets.TransparentButton("Transparent", "edit"),
            lambda: mywidgets.ToggleButton("Toggle", "check"),
            lambda: mywidgets.DropDownButton("Menu", "menu", menu),
            lambda: mywidgets.PrimarySplitButton("Send", "send", menu),
            lambda: mywidgets.PillButton("Filter", "filter"),
            lambda: mywidgets.TextInput("value"),
            lambda: mywidgets.PasswordInput("secret"),
            lambda: mywidgets.NumberInput(3),
            lambda: mywidgets.DoubleNumberInput(1.25),
            lambda: mywidgets.ComboSelect(["A", "B"]),
            lambda: mywidgets.DatePicker(),
            lambda: mywidgets.CalendarPicker(),
            lambda: mywidgets.MonthPicker(),
            lambda: mywidgets.TimePicker(),
            lambda: mywidgets.DateTimePicker(),
            lambda: mywidgets.HeaderCard("Header", icon="settings"),
            lambda: mywidgets.Pagination(3, 0),
            lambda: mywidgets.ModernList(["A"]),
            lambda: mywidgets.ModernTree(["Root"]),
            lambda: mywidgets.ModernTabs(),
            lambda: mywidgets.OptionsSettingCard("Mode", ["A", "B"]),
            lambda: mywidgets.ExpandSettingCard("Advanced"),
            lambda: mywidgets.FolderListSettingCard("Folders", []),
        ]
        widgets = [factory() for factory in factories]
        mywidgets.apply_theme(self.app, mywidgets.ThemeMode.DARK, "#00a389")
        self.app.processEvents()
        self.assertTrue(all(widget is not None for widget in widgets))
        for widget in widgets:
            widget.deleteLater()

    def test_date_defaults_use_current_values(self):
        today = QDate.currentDate()
        now = QTime.currentTime()
        self.assertEqual(mywidgets.DatePicker().date(), today)
        self.assertEqual(mywidgets.CalendarPicker().date(), today)
        self.assertEqual(
            mywidgets.MonthPicker().date(),
            QDate(today.year(), today.month(), 1),
        )
        self.assertLess(abs(now.secsTo(mywidgets.TimePicker().time())), 3)

    def test_navigation_and_gallery_smoke(self):
        window = GalleryWindow()
        window.resize(980, 640)
        window.show()
        self.app.processEvents()
        self.assertEqual(window.stack.count(), 6)
        self.assertEqual(window.route_key(5), "settings")
        self.assertFalse(window.windowIcon().isNull())
        for index in range(window.stack.count()):
            self.assertTrue(window.set_current(index))
            self.app.processEvents()
        self.assertTrue(window.set_current("basics"))
        self.assertFalse(window.set_current("missing"))
        window.close()

    def test_navigation_mutations_preserve_and_report_selection(self):
        top = mywidgets.TopNavigation()
        for title in ("A", "B", "C"):
            top.add_item(title, "home")
        top.set_current(0)
        top_events = []
        top.currentChanged.connect(top_events.append)
        top.remove_item(2)
        self.assertEqual(0, next(item.index for item in top._items if item.isChecked()))
        self.assertEqual([], top_events)
        top.remove_item(0)
        self.assertEqual(0, next(item.index for item in top._items if item.isChecked()))
        self.assertEqual([0], top_events)

        side = mywidgets.SideNavigation()
        for index, title in enumerate(("A", "B", "C")):
            side.add_item(index, title, "home")
        side.set_current(2)
        side_events = []
        side.currentChanged.connect(side_events.append)
        side.remove_item(0)
        self.assertEqual(1, next(item.index for item in side._items if item.isChecked()))
        self.assertEqual([1], side_events)
        side.clear()
        self.assertEqual([1, -1], side_events)

        segmented = mywidgets.SegmentedControl(["A", "B", "C"])
        segmented.set_current(2)
        segmented_events = []
        segmented.currentChanged.connect(segmented_events.append)
        segmented.remove_item(0)
        self.assertEqual(1, segmented.current_index())
        segmented.remove_item(1)
        self.assertEqual(0, segmented.current_index())
        self.assertEqual([1, 0], segmented_events)

        window = mywidgets.ModernWindow()
        for route in ("a", "b", "c"):
            window.add_page(QWidget(), route, "home", route_key=route)
        window.set_current("b")
        window_events = []
        window.currentChanged.connect(window_events.append)
        window.remove_page("b")
        self.assertEqual("c", window.route_key(window.stack.currentIndex()))
        self.assertEqual([1], window_events)
        window.remove_page("a")
        self.assertEqual("c", window.route_key(window.stack.currentIndex()))
        self.assertEqual([1, 0], window_events)

    def test_input_icon_refresh_reuses_actions(self):
        password = mywidgets.PasswordInput("secret")
        search = mywidgets.SearchInput()
        initial = (
            len(password.findChildren(QAction)),
            len(search.findChildren(QAction)),
        )
        for index in range(8):
            mode = mywidgets.ThemeMode.DARK if index % 2 else mywidgets.ThemeMode.LIGHT
            mywidgets.apply_theme(self.app, mode)
            password._toggle_password()
        self.assertEqual(
            initial,
            (
                len(password.findChildren(QAction)),
                len(search.findChildren(QAction)),
            ),
        )

    def test_flyout_and_toast_positions(self):
        host = QWidget()
        host.resize(500, 400)
        host.move(100, 100)
        anchor = QPushButton("Anchor", host)
        anchor.setGeometry(200, 170, 80, 30)
        host.show()
        anchor.show()
        self.app.processEvents()
        origin = anchor.mapToGlobal(QPoint())

        expected = {
            mywidgets.PopupPosition.TOP_LEFT: lambda popup: QPoint(
                origin.x(), origin.y() - popup.height() - 8
            ),
            mywidgets.PopupPosition.TOP_RIGHT: lambda popup: QPoint(
                origin.x() + anchor.width() - popup.width(),
                origin.y() - popup.height() - 8,
            ),
            mywidgets.PopupPosition.BOTTOM_LEFT: lambda popup: QPoint(
                origin.x(), origin.y() + anchor.height() + 8
            ),
            mywidgets.PopupPosition.BOTTOM_RIGHT: lambda popup: QPoint(
                origin.x() + anchor.width() - popup.width(),
                origin.y() + anchor.height() + 8,
            ),
            mywidgets.PopupPosition.CENTER: lambda popup: QPoint(
                origin.x() + (anchor.width() - popup.width()) // 2,
                origin.y() + (anchor.height() - popup.height()) // 2,
            ),
        }
        for position, position_for in expected.items():
            popup = mywidgets.Flyout.show_at(anchor, "Title", "Content", position)
            self.app.processEvents()
            self.assertEqual(position_for(popup), popup.pos(), position.value)
            popup.close()

        toast = mywidgets.ToastManager.show(
            host,
            "Center",
            "Content",
            duration=0,
            position=mywidgets.PopupPosition.CENTER,
        )
        self.app.processEvents()
        self.assertEqual((host.width() - toast.width()) // 2, toast.x())
        self.assertEqual((host.height() - toast.height()) // 2, toast.y())
        host.close()

    def test_toast_manager_drops_destroyed_hosts(self):
        host = QWidget()
        mywidgets.ToastManager.info(host, "Title", "Content", duration=0)
        self.assertIn(host, mywidgets.ToastManager._active)
        self.assertIn(host, mywidgets.ToastManager._filters)
        host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertNotIn(host, mywidgets.ToastManager._active)
        self.assertNotIn(host, mywidgets.ToastManager._filters)

    def test_layout_state_and_pagination_boundaries(self):
        host = QWidget()
        flow = mywidgets.FlowLayout(host, spacing=10)
        hidden = QPushButton("Hidden")
        visible = QPushButton("Visible")
        flow.addWidget(hidden)
        flow.addWidget(visible)
        hidden.hide()
        flow.setGeometry(QRect(0, 0, 300, 100))
        self.assertEqual(0, visible.geometry().x())

        expand = mywidgets.ExpandSettingCard("Advanced")
        expanded_events = []
        expand.expandedChanged.connect(expanded_events.append)
        expand.set_expanded(False)
        expand.set_expanded(False)
        expand.set_expanded(True)
        expand.set_expanded(True)
        self.assertEqual([True], expanded_events)

        tabs = mywidgets.ModernTabs()
        closed_events = []
        tabs.tabClosed.connect(closed_events.append)
        self.assertFalse(tabs._close_tab(99))
        tabs.addTab(QWidget(), "A")
        self.assertTrue(tabs._close_tab(0))
        self.assertEqual([0], closed_events)

        pagination = mywidgets.Pagination(5, 4)
        page_events = []
        pagination.currentChanged.connect(page_events.append)
        pagination.set_page_count(2)
        self.assertEqual(1, pagination.current_index())
        pagination.remove_item(0)
        self.assertEqual(0, pagination.current_index())
        self.assertEqual([1, 0], page_events)

        grid = mywidgets.CardGrid()
        card = QWidget()
        grid.add_card(card)
        grid.add_card(card)
        self.assertEqual([card], grid._cards)

    def test_clickable_slider_only_jumps_for_left_button(self):
        slider = mywidgets.ClickableSlider()
        slider.setRange(0, 100)
        slider.resize(200, 30)
        slider.setValue(25)
        slider.show()
        self.app.processEvents()
        QTest.mouseClick(slider, Qt.RightButton, Qt.NoModifier, QPoint(150, 15))
        self.assertEqual(25, slider.value())
        QTest.mouseClick(slider, Qt.LeftButton, Qt.NoModifier, QPoint(150, 15))
        self.assertEqual(75, slider.value())

    def test_state_tooltip_can_cancel_pending_close(self):
        tooltip = mywidgets.StateTooltip("Working")
        tooltip.show()
        tooltip.set_state(True, "Done", duration=40)
        tooltip.set_state(False, "Keep open", duration=0)
        QTest.qWait(70)
        self.assertTrue(tooltip.isVisible())
        tooltip.close()

    def test_command_bar_overflow_keeps_button_connections(self):
        bar = mywidgets.CommandBar()
        buttons = [bar.add_action(f"Action {index}", "info") for index in range(6)]
        calls = []
        buttons[-1].clicked.connect(lambda checked=False: calls.append("last"))
        bar.resize(180, 40)
        bar.show()
        self.app.processEvents()
        bar._update_overflow()
        actions = bar._overflow_menu.actions()
        self.assertGreater(len(actions), 0)
        overflow_action = next(action for action in actions if action.text() == "Action 5")
        overflow_action.trigger()
        self.assertEqual(["last"], calls)

        bar.resize(2000, 40)
        self.app.processEvents()
        bar._update_overflow()
        self.assertTrue(all(button.isVisible() for button in buttons))
        self.assertTrue(bar._overflow_menu.isEmpty())
        bar.close()

    def test_color_setting_card_tracks_current_color(self):
        card = mywidgets.ColorSettingCard(
            "Accent",
            ["#111111", "#222222", "#333333"],
            current="#222222",
        )
        self.assertEqual("#222222", card.current())
        self.assertTrue(card.set_current("#333333"))
        self.assertEqual("#333333", card.current())
        self.assertFalse(card.set_current("#ffffff"))

    def test_image_view_clears_invalid_source(self):
        pixmap = QPixmap(24, 12)
        pixmap.fill(QColor("#3f8cff"))
        view = mywidgets.ImageView(pixmap)
        view.resize(120, 80)
        view.show()
        self.app.processEvents()
        self.assertFalse(view.pixmap().isNull())
        view.set_source(PROJECT_ROOT / "does-not-exist.png")
        self.assertTrue(view.pixmap().isNull())
        view.close()

    def test_config_store_handles_non_object_json_and_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text('["valid", "json", "but", "not", "an", "object"]', encoding="utf-8")
            store = mywidgets.ConfigStore(path)
            self.assertEqual({}, store.data)
            store.update({"主题": "dark", "timeout": 30})
            self.assertEqual("dark", store.get("主题"))
            self.assertTrue(store.clear())
            self.assertEqual({}, store.data)
            self.assertFalse(store.clear())

    def test_copied_package_imports_without_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "mywidgets"
            shutil.copytree(
                PROJECT_ROOT / "mywidgets",
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            environment = os.environ.copy()
            environment["QT_QPA_PLATFORM"] = "offscreen"
            environment.pop("PYTHONPATH", None)
            code = (
                "from PySide6.QtWidgets import QApplication; "
                "from mywidgets import DatePicker, ThemeMode, apply_theme; "
                "app=QApplication([]); apply_theme(app, ThemeMode.DARK); "
                "print(DatePicker().date().isValid())"
            )
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("True", result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
