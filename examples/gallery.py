"""Interactive showcase for the public :mod:`mywidgets` API.

Run from the repository root with ``python examples/gallery.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QStringListModel, QTimer
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QTableWidgetItem,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mywidgets import (
    AdaptiveFlowLayout,
    AmPmTimePicker,
    Avatar,
    BodyText,
    BreadcrumbBar,
    CalendarPicker,
    Card,
    CardGrid,
    CheckBox,
    CheckableMenu,
    ClickableCard,
    ColorDialog,
    ColorSettingCard,
    ComboSelect,
    CommandBar,
    DataTable,
    DataTableView,
    DatePicker,
    DateTimePicker,
    DisplayText,
    DotBadge,
    DoubleNumberInput,
    DropDownButton,
    EditableComboSelect,
    ElevatedCard,
    EmptyState,
    ExpandSettingCard,
    Flyout,
    FolderListDialog,
    FolderListSettingCard,
    HeaderCard,
    HyperlinkButton,
    HyperlinkSettingCard,
    HyperlinkText,
    IndeterminateProgressLine,
    IndeterminateProgressRing,
    InfoBadge,
    InfoBanner,
    LargeTitleText,
    LoadingPanel,
    MessageBox,
    MetricCard,
    ModernList,
    ModernListView,
    ModernMenu,
    ModernTabs,
    ModernTree,
    ModernTreeView,
    ModernWindow,
    MonthPicker,
    NumberInput,
    OptionsSettingCard,
    Pagination,
    PasswordInput,
    PillButton,
    PivotControl,
    PlainTextArea,
    PrimaryButton,
    PrimaryDropDownButton,
    PrimarySplitButton,
    PrimaryToolButton,
    ProgressLine,
    ProgressRing,
    PushSettingCard,
    RadioButton,
    RangeSettingCard,
    ScrollablePanel,
    SearchInput,
    SecondaryButton,
    SegmentedControl,
    SettingGroup,
    SplashScreen,
    StateTooltip,
    StatusBadge,
    StrongText,
    SubtitleText,
    SwitchSettingCard,
    TeachingTip,
    TextArea,
    TextInput,
    ThemeManager,
    ThemeMode,
    TimePicker,
    TitleText,
    ToastManager,
    ToggleButton,
    ToggleSwitch,
    ToggleToolButton,
    TopNavigation,
    TransparentButton,
    TransparentToolButton,
    apply_theme,
)


DEFAULT_ACCENT = "#3f8cff"


class GalleryPage(ScrollablePanel):
    """Scrollable page with consistent headings and section cards."""

    def __init__(self, title: str, subtitle: str, parent=None):
        content = QWidget()
        content.setObjectName("GalleryPage")
        super().__init__(content, parent)
        self.root = QVBoxLayout(content)
        self.root.setContentsMargins(32, 26, 32, 32)
        self.root.setSpacing(18)
        self.root.addWidget(TitleText(title))
        description = BodyText(subtitle)
        description.setWordWrap(True)
        self.root.addWidget(description)

    def add_section(self, title: str, content: str = "", icon=None) -> HeaderCard:
        section = HeaderCard(title, content, icon)
        self.root.addWidget(section)
        return section

    def finish(self):
        self.root.addStretch(1)


def flow_host(widgets: list[QWidget], minimum_item_width: int = 0) -> QWidget:
    host = QWidget()
    flow = AdaptiveFlowLayout(
        host,
        spacing=10,
        minimum_item_width=minimum_item_width,
    )
    for widget in widgets:
        flow.addWidget(widget)
    return host


class BasicsPage(GalleryPage):
    def __init__(self, parent=None):
        super().__init__("基础控件", "文字层级、按钮、选择状态、徽章、卡片与头像。", parent)

        typography = self.add_section("文字层级", icon="edit")
        typography.add_widget(DisplayText("Display / 展示文字"))
        typography.add_widget(LargeTitleText("Large title / 大标题"))
        typography.add_widget(SubtitleText("Subtitle / 副标题"))
        typography.add_widget(BodyText("正文用于承载稳定、易扫描的信息内容。"))
        typography.add_widget(HyperlinkText("Qt for Python 文档", "https://doc.qt.io/qtforpython-6/"))

        menu = ModernMenu("常用操作", self)
        menu.add_command("保存", "save")
        menu.add_command("复制", "copy")
        menu.add_command("删除", "delete")
        buttons = self.add_section("按钮族", "按钮支持主题、禁用、焦点和键盘状态。", "check")
        buttons.add_widget(
            flow_host(
                [
                    PrimaryButton("主要操作", "send"),
                    SecondaryButton("次要操作", "save"),
                    TransparentButton("透明按钮", "edit"),
                    ToggleButton("切换按钮", "check"),
                    PillButton("筛选条件", "filter"),
                    HyperlinkButton("访问 Qt", "https://www.qt.io"),
                    DropDownButton("下拉按钮", "menu", menu),
                    PrimaryDropDownButton("主要下拉", "add", menu),
                    PrimarySplitButton("发送请求", "send", menu),
                    PrimaryToolButton("add", "新建"),
                    TransparentToolButton("edit", "编辑"),
                    ToggleToolButton("pin", "固定"),
                ]
            )
        )

        state = self.add_section("选择与状态", icon="info")
        switch = ToggleSwitch()
        switch.setAccessibleName("启用通知")
        state.add_widget(
            flow_host(
                [
                    CheckBox("记住选择"),
                    RadioButton("使用系统设置"),
                    switch,
                    InfoBadge("NEW"),
                    StatusBadge("成功", "success"),
                    StatusBadge("警告", "warning"),
                    StatusBadge("错误", "error"),
                    DotBadge("info"),
                ]
            )
        )

        cards = CardGrid(3)
        for card_type, title in (
            (ClickableCard, "可点击卡片"),
            (ElevatedCard, "悬浮卡片"),
        ):
            card = card_type()
            layout = QVBoxLayout(card)
            layout.setContentsMargins(18, 16, 18, 16)
            layout.addWidget(StrongText(title))
            layout.addWidget(BodyText("适合轻量入口与摘要信息。"))
            cards.add_card(card)
        avatar_card = Card()
        avatar_layout = QHBoxLayout(avatar_card)
        avatar_layout.setContentsMargins(18, 16, 18, 16)
        avatar_layout.addWidget(Avatar("MW", diameter=48))
        avatar_layout.addWidget(BodyText("头像与身份信息"))
        avatar_layout.addStretch(1)
        cards.add_card(avatar_card)
        self.root.addWidget(cards)
        self.finish()


class InputsPage(GalleryPage):
    def __init__(self, parent=None):
        super().__init__("输入与选择", "文本、数值、选择器、日期时间以及输入状态。", parent)

        form = self.add_section("表单控件", icon="edit")
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)
        grid.addWidget(TextInput("https://api.example.com/v1/orders"), 0, 0)
        grid.addWidget(PasswordInput("secret-token"), 0, 1)
        grid.addWidget(NumberInput(30), 1, 0)
        grid.addWidget(DoubleNumberInput(3.14), 1, 1)
        search = SearchInput()
        search.setPlaceholderText("搜索接口")
        grid.addWidget(search, 2, 0)
        grid.addWidget(ComboSelect(["GET", "POST", "PUT", "DELETE"]), 2, 1)
        grid.addWidget(EditableComboSelect(["dev", "staging", "prod"]), 3, 0, 1, 2)
        grid.addWidget(TextArea('{\n  "hello": "world"\n}'), 4, 0)
        grid.addWidget(PlainTextArea("纯文本输入区域"), 4, 1)
        form.body.addLayout(grid)

        dates = self.add_section("日期与时间", icon="calendar")
        dates.add_widget(
            flow_host(
                [
                    DatePicker(),
                    CalendarPicker(),
                    MonthPicker(),
                    TimePicker(),
                    AmPmTimePicker(),
                    DateTimePicker(),
                ],
                minimum_item_width=150,
            )
        )
        self.finish()


class DataPage(GalleryPage):
    def __init__(self, parent=None):
        super().__init__("数据展示", "指标、进度、分页、表格、列表、树和模型视图。", parent)

        metrics = CardGrid(3)
        metrics.add_card(MetricCard("send", "今日请求", "1,284", "近 24 小时", 82))
        metrics.add_card(MetricCard("time", "平均耗时", "142 ms", "P95 保持稳定", 64))
        metrics.add_card(MetricCard("success", "成功率", "99.2%", "服务运行正常", 96))
        self.root.addWidget(metrics)

        progress = self.add_section("进度与分页", icon="time")
        progress.add_widget(
            flow_host(
                [
                    ProgressRing(72),
                    IndeterminateProgressRing(),
                    ProgressLine(68),
                    IndeterminateProgressLine(),
                    Pagination(12, 2),
                ],
                minimum_item_width=80,
            )
        )

        table = DataTable()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["接口", "状态", "耗时"])
        values = [("登录", "200", "96 ms"), ("订单", "200", "121 ms"), ("短信", "429", "41 ms")]
        table.setRowCount(len(values))
        for row, row_values in enumerate(values):
            for column, value in enumerate(row_values):
                table.setItem(row, column, QTableWidgetItem(value))
        table.setMinimumHeight(180)
        self.root.addWidget(table)

        views = self.add_section("列表、树和模型视图", icon="api")
        row = QGridLayout()
        modern_list = ModernList(["开发环境", "测试环境", "生产环境"])
        tree = ModernTree(["服务"])
        root = QTreeWidgetItem(["订单服务"])
        root.addChildren([QTreeWidgetItem(["/v1/orders"]), QTreeWidgetItem(["/v1/payments"])])
        tree.addTopLevelItem(root)
        tree.expandAll()
        list_view = ModernListView()
        list_view.setModel(QStringListModel(["Model A", "Model B", "Model C"]))
        tree_view = ModernTreeView()
        tree_model = QStandardItemModel()
        service = QStandardItem("用户服务")
        service.appendRow(QStandardItem("/v1/users"))
        tree_model.appendRow(service)
        tree_view.setModel(tree_model)
        table_view = DataTableView()
        table_model = QStandardItemModel(2, 2)
        table_model.setHorizontalHeaderLabels(["名称", "值"])
        table_model.setItem(0, 0, QStandardItem("环境"))
        table_model.setItem(0, 1, QStandardItem("生产"))
        table_view.setModel(table_model)
        for index, widget in enumerate((modern_list, tree, list_view, tree_view, table_view)):
            widget.setMinimumHeight(150)
            row.addWidget(widget, index // 3, index % 3)
        views.body.addLayout(row)
        self.finish()


class NavigationPage(GalleryPage):
    def __init__(self, parent=None):
        super().__init__("导航", "分段、Pivot、面包屑、顶部导航、标签页和响应式命令栏。", parent)

        local = self.add_section("局部导航", icon="menu")
        local.add_widget(SegmentedControl(["概览", "接口", "历史", "设置"]))
        local.add_widget(PivotControl(["请求", "响应", "日志"]))
        local.add_widget(BreadcrumbBar(["项目", "接口集合", "订单服务"]))
        top = TopNavigation()
        top.add_item("首页", "home")
        top.add_item("历史", "history")
        top.add_item("设置", "settings")
        local.add_widget(top)

        command = CommandBar()
        for text, icon in (("新建", "add"), ("保存", "save"), ("复制", "copy"), ("刷新", "refresh"), ("删除", "delete")):
            command.add_action(text, icon, primary=text == "新建")
        self.root.addWidget(command)

        tabs = ModernTabs()
        tabs.set_tabs_closable(True)
        tabs.set_tabs_movable(True)
        tabs.addTab(EmptyState("请求正文", "可关闭、可移动的工作区标签。"), "请求")
        tabs.addTab(LoadingPanel("正在读取响应"), "响应")
        tabs.setMinimumHeight(230)
        self.root.addWidget(tabs)
        self.finish()


class FeedbackPage(GalleryPage):
    def __init__(self, parent=None):
        super().__init__("反馈与弹层", "通知、菜单、对话框、Flyout、TeachingTip 与状态提示。", parent)

        self.root.addWidget(
            InfoBanner("环境已同步", "配置已写入本地，可以继续调试。", kind="success", closable=True)
        )
        self.checkable_menu = CheckableMenu("环境", exclusive=True, parent=self)
        self.checkable_menu.add_checkable("开发", True)
        self.checkable_menu.add_checkable("测试")
        self.checkable_menu.add_checkable("生产")

        bar = CommandBar()
        bar.add_action("Toast", "info", lambda: ToastManager.info(self.window(), "普通提示", "这是一条本地通知。"))
        bar.add_action("成功", "success", lambda: ToastManager.success(self.window(), "请求完成", "响应耗时 128 ms"))
        bar.add_action("Dialog", "info", self.show_dialog, primary=True)
        flyout_button = bar.add_action("Flyout", "menu")
        flyout_button.clicked.connect(lambda: Flyout.show_at(flyout_button, "更多操作", "弹层会自动避开屏幕边缘。"))
        tip_button = bar.add_action("TeachingTip", "warning")
        tip_button.clicked.connect(lambda: TeachingTip.show_at(tip_button, "新功能", "这里可以解释重点入口。"))
        bar.add_action("菜单", "menu", self.show_menu)
        bar.add_action("状态", "time", self.show_state_tooltip)
        bar.add_action("颜色", "palette", self.show_color_dialog)
        bar.add_action("文件夹", "folder", self.show_folder_dialog)
        bar.add_action("启动屏", "rocket", self.show_splash)
        self.root.addWidget(bar)
        self.root.addWidget(EmptyState("暂无更多消息", "所有弹层都可以在亮色与暗色主题下使用。"))
        self.finish()

    def show_menu(self):
        self.checkable_menu.popup(self.mapToGlobal(self.rect().center()))

    def show_dialog(self):
        MessageBox("确认操作", "这是一个使用 mywidgets 实现的现代对话框。", self.window()).exec()

    def show_color_dialog(self):
        ColorDialog(parent=self.window()).open()

    def show_folder_dialog(self):
        FolderListDialog(paths=[str(PROJECT_ROOT)], parent=self.window()).open()

    def show_state_tooltip(self):
        tooltip = StateTooltip("正在同步", "请稍候", self.window())
        tooltip.adjustSize()
        center = self.window().mapToGlobal(self.window().rect().center())
        tooltip.move(center - tooltip.rect().center())
        tooltip.show()
        QTimer.singleShot(800, lambda: tooltip.set_state(True, "同步完成"))

    def show_splash(self):
        splash = SplashScreen("正在初始化工作区", parent=self.window())
        splash.show()
        splash.raise_()
        QTimer.singleShot(1000, splash.close)


class SettingsPage(GalleryPage):
    def __init__(self, parent=None):
        super().__init__("设置", "主题、选项、范围、颜色、链接、展开内容和文件夹列表。", parent)

        appearance = SettingGroup("外观")
        self.theme_card = SwitchSettingCard("深色模式", "即时切换应用主题", "settings")
        self.theme_card.checkedChanged.connect(self.toggle_theme)
        appearance.add_card(self.theme_card)
        color_card = ColorSettingCard(
            "强调色",
            ["#3f8cff", "#00a389", "#d83b01", "#c239b3", "#8764b8"],
            "选择应用主色",
            current=ThemeManager.instance().accent,
        )
        color_card.colorChanged.connect(self.set_accent)
        appearance.add_card(color_card)
        appearance.add_card(RangeSettingCard("默认超时", "单位：秒", "time", 5, 120, 30))
        appearance.add_card(OptionsSettingCard("界面密度", ["紧凑", "标准", "宽松"], "选择控件间距", "menu", "标准"))
        appearance.add_card(PushSettingCard("重置外观", "重置", "恢复默认主题", "refresh"))
        appearance.add_card(
            HyperlinkSettingCard(
                "组件文档",
                "查看 Qt 文档",
                "https://doc.qt.io/qtforpython-6/",
                "外部参考",
                "link",
            )
        )
        self.root.addWidget(appearance)

        advanced = SettingGroup("高级")
        expand = ExpandSettingCard("请求策略", "展开查看说明", "api", True)
        expand.add_widget(BodyText("失败请求最多重试两次，并使用指数退避。"))
        advanced.add_card(expand)
        advanced.add_card(FolderListSettingCard("工作目录", [str(PROJECT_ROOT)], "管理扫描路径"))
        self.root.addWidget(advanced)

        ThemeManager.instance().themeChanged.connect(self.sync_theme_switch)
        self.sync_theme_switch(ThemeManager.instance().palette)
        self.finish()

    def toggle_theme(self, checked: bool):
        manager = ThemeManager.instance()
        apply_theme(QApplication.instance(), ThemeMode.DARK if checked else ThemeMode.LIGHT, manager.accent)

    def set_accent(self, color: str):
        manager = ThemeManager.instance()
        apply_theme(QApplication.instance(), manager.mode, color)

    def sync_theme_switch(self, palette):
        self.theme_card.switch.blockSignals(True)
        self.theme_card.switch.setChecked(palette.mode == ThemeMode.DARK)
        self.theme_card.switch.blockSignals(False)


class GalleryWindow(ModernWindow):
    def __init__(self):
        super().__init__("mywidgets Gallery", "MYWIDGETS")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)
        self.navigation.add_header("组件")
        self.add_page(BasicsPage(self), "基础控件", "home", route_key="basics")
        self.add_page(InputsPage(self), "输入选择", "edit", route_key="inputs")
        self.add_page(DataPage(self), "数据展示", "api", route_key="data")
        self.add_page(NavigationPage(self), "导航", "menu", route_key="navigation")
        self.add_page(FeedbackPage(self), "反馈弹层", "info", route_key="feedback")
        self.navigation.add_separator("bottom")
        self.add_page(SettingsPage(self), "设置", "settings", position="bottom", route_key="settings")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the mywidgets component gallery.")
    parser.add_argument("--dark", action="store_true", help="Start with the dark theme.")
    parser.add_argument("--accent", default=DEFAULT_ACCENT, help="Theme accent color.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args, qt_args = build_parser().parse_known_args(argv)
    app = QApplication.instance() or QApplication([sys.argv[0], *qt_args])
    apply_theme(app, ThemeMode.DARK if args.dark else ThemeMode.LIGHT, args.accent)
    window = GalleryWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
