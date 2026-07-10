# mywidgets

`mywidgets` is a PySide6 widget library with Fluent-style desktop controls, theme support, icon recoloring, CJK font discovery, dialogs, menus, settings cards, date/time controls, navigation, data views, and a small Gallery example.

It has no runtime dependency on `qfluentwidgets`.

## Install

```bash
python -m pip install mywidgets
```

For local development from this repository:

```bash
python -m pip install -e .
```

## Minimal Usage

```python
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from mywidgets import BodyText, ModernWindow, PrimaryButton, ThemeMode, apply_theme


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(BodyText("mywidgets is ready"))
        layout.addWidget(PrimaryButton("Run", "play"))
        layout.addStretch(1)


app = QApplication(sys.argv)
apply_theme(app, ThemeMode.LIGHT, "#3f8cff")

window = ModernWindow("Tool", "MY TOOL")
window.add_page(HomePage(), "Home", "home", route_key="home")
window.resize(1100, 720)
window.show()
sys.exit(app.exec())
```

More examples are in `mywidgets/USAGE.md` and `app/gallery.py`.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q mywidgets app tests
python -m build
python -m twine check dist/*
```

## Package Contents

- `mywidgets/`: distributable Python package.
- `app/gallery.py`: interactive Gallery example for development.
- `examples/gallery.py`: lightweight example launcher.
- `tests/`: standard `unittest` test suite.
