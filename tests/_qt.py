import os


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


def get_app():
    return QApplication.instance() or QApplication([])
