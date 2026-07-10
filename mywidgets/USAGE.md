# mywidgets 使用指南

本文随 `mywidgets/` 包一起发布，用于在其他 PySide6 项目中快速接入组件库。

## 1. 环境与安装

- Python 3.10+
- PySide6 6.6+
- QtAwesome 1.3+

推荐从 PyPI 安装：

```bash
python -m pip install mywidgets
```

如果采用源码复制方式，应复制整个 `mywidgets/` 目录，并安装依赖：

```bash
python -m pip install -r mywidgets/requirements.txt
```

使用源码复制方式时，应保持 `mywidgets/` 包内文件版本一致，不要混用不同版本的模块文件。

## 2. 应用初始化

必须按以下顺序初始化：创建 `QApplication`、应用主题、创建窗口和控件。

```python
import sys

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from mywidgets import BodyText, ModernWindow, PrimaryButton, ThemeMode, apply_theme


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(BodyText("mywidgets 已接入"))
        layout.addWidget(PrimaryButton("执行", "play"))
        layout.addStretch(1)


app = QApplication(sys.argv)
apply_theme(app, ThemeMode.LIGHT, "#3f8cff")

window = ModernWindow("工具", "MY TOOL")
window.add_page(HomePage(), "首页", "home", route_key="home")
window.resize(1100, 720)
window.show()
sys.exit(app.exec())
```

推荐从 `mywidgets` 根包导入公开组件。`mywidgets.widgets` 和 `mywidgets.controls` 仅用于兼容已有项目。

## 3. 主题切换

```python
from PySide6.QtWidgets import QApplication
from mywidgets import ThemeManager, ThemeMode, apply_theme


app = QApplication.instance()
apply_theme(app, ThemeMode.DARK, "#00a389")

# 在亮色和暗色之间切换
ThemeManager.instance().toggle(app)

# 跟随系统颜色方案
apply_theme(app, ThemeMode.AUTO, "#3f8cff")
```

`apply_theme()` 会更新应用级样式表。不要在其后直接用 `app.setStyleSheet()` 覆盖全局样式；项目自定义样式应限定对象名，并在 `ThemeManager.themeChanged` 后重新应用。

## 4. 表单与日期时间

```python
from PySide6.QtWidgets import QFormLayout, QWidget
from mywidgets import (
    CalendarPicker,
    ComboSelect,
    DateTimePicker,
    NumberInput,
    PasswordInput,
    SearchInput,
    TextInput,
)


form_widget = QWidget()
form = QFormLayout(form_widget)
form.addRow("地址", TextInput("https://api.example.com"))
form.addRow("令牌", PasswordInput())
form.addRow("方法", ComboSelect(["GET", "POST", "PUT", "DELETE"]))
form.addRow("超时", NumberInput(30))
form.addRow("搜索", SearchInput())
form.addRow("日期", CalendarPicker())
form.addRow("时间戳", DateTimePicker())
```

日期和时间控件保持 `QDateEdit`、`QTimeEdit`、`QDateTimeEdit` 接口，可继续使用 `setDate()`、`setTime()`、`dateChanged` 和 `timeChanged`。默认值为当前日期时间，`MonthPicker.date()` 的日期部分固定为 1 日。

## 5. 反馈与弹层

```python
from mywidgets import Flyout, MessageBox, ToastManager


ToastManager.success(window, "完成", "配置已保存")
MessageBox("确认", "是否继续执行？", window).exec()
Flyout.show_at(button, "更多操作", "弹层会自动限制在屏幕可用区域内。")
```

Toast、Dialog 和 Flyout 应传入当前窗口或锚点控件作为父对象，避免弹层位置错误或对象被提前回收。

## 6. 设置与配置

```python
from pathlib import Path

from mywidgets import ConfigStore, SettingGroup, SwitchSettingCard


settings = SettingGroup("常规")
settings.add_card(SwitchSettingCard("自动保存", "退出前保存工作区", "save"))

store = ConfigStore(Path.home() / ".my_tool" / "settings.json")
store.set("theme", "dark")
store.update({"accent": "#3f8cff", "timeout": 30})
```

`ConfigStore` 使用 UTF-8 JSON 和原子替换写入。无效或损坏的 JSON 会回退为空配置。

## 7. 图标

组件图标参数接受 `mywidgets` 内置别名、QtAwesome 名称、`IconSpec` 或 `QIcon`：

```python
from mywidgets import IconSpec, PrimaryButton, ToolButton


save_button = PrimaryButton("保存", "save")
python_button = ToolButton("fa5b.python", "Python")
warning_button = ToolButton(IconSpec("warning", "warning"), "警告")
```

内置别名包括 `add`、`back`、`calendar`、`check`、`close`、`copy`、`delete`、`edit`、`folder`、`home`、`info`、`menu`、`save`、`search`、`send`、`settings`、`success`、`time`、`warning` 等。

## 8. 常见问题

### 中文显示为方框

`apply_theme()` 会尝试注册 Windows、Linux 和 macOS 常见中文字体。精简系统若完全没有 CJK 字体，需要先安装 Microsoft YaHei、Noto Sans SC 或其他中文字体。

### 主题没有生效

确认 `QApplication` 已创建，并且没有在 `apply_theme()` 后用其他全局样式表覆盖应用样式。主题切换必须在 GUI 主线程执行。

### 弹层位置异常

为 Toast 和 Dialog 传入顶层窗口，为 Flyout 和 TeachingTip 传入屏幕上可见的锚点控件。

### 项目有自己的资源目录

业务资源路径应基于业务模块的 `__file__` 解析，不要依赖当前工作目录。`mywidgets` 自身不要求复制 Gallery 图片。

### 更新 mywidgets

先备份业务侧对 `mywidgets` 的直接修改，再整体替换目录或升级 PyPI 版本。不要把新旧版本模块混合复制；公开导入应集中在业务项目的 UI 适配层，便于后续升级。
