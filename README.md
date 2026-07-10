# mywidgets

`mywidgets` 是一个基于 PySide6 的 Fluent 风格桌面组件库，提供亮色/暗色/跟随系统主题、动态图标、导航、输入、数据展示、反馈弹层、设置卡片和日期时间控件。

公开组件统一从 `mywidgets` 根包导入。

## 安装

```bash
python -m pip install mywidgets
```

从源码开发：

```bash
git clone https://github.com/zhuangjinpo06/mywidgets.git
cd mywidgets
python -m pip install -e ".[dev]"
```

## 快速开始

```python
import sys

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from mywidgets import BodyText, ModernWindow, PrimaryButton, ThemeMode, apply_theme


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(BodyText("mywidgets 已就绪"))
        layout.addWidget(PrimaryButton("运行", "play"))
        layout.addStretch(1)


app = QApplication(sys.argv)
apply_theme(app, ThemeMode.LIGHT, "#3f8cff")

window = ModernWindow("示例应用", "MY APP")
window.add_page(HomePage(), "首页", "home", route_key="home")
window.resize(1100, 720)
window.show()
sys.exit(app.exec())
```

## Gallery

Gallery 覆盖基础控件、表单、日期时间、数据视图、导航、弹层和设置组件：

```bash
python examples/gallery.py
python examples/gallery.py --dark
python examples/gallery.py --accent "#00a389"
```

## 开发与验证

```bash
python -m unittest discover -s tests -v
python -m compileall -q mywidgets examples tests
python -m build
python -m twine check dist/*
```

更完整的接入说明见 [mywidgets/USAGE.md](mywidgets/USAGE.md)。

## 项目结构

- `mywidgets/`：可发布的组件库。
- `examples/gallery.py`：可交互的完整组件 Gallery。
- `tests/`：离屏 Qt 自动化测试。
- `.github/workflows/`：持续集成与 PyPI Trusted Publishing 工作流。
