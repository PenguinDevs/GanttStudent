"""Project view module."""

import os

from PyQt6.QtWidgets import(
    QApplication,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    
)
from PyQt6 import uic
from qt_async_threads import QtAsyncRunner

import config


class ProjectViewWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._load_ui()
        self._assign_window_properties()

    def _load_ui(self):
        return uic.load_ui.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\project_view_window.ui"), self)

    def _assign_window_properties(self):
        pass

class ProjectViewController:
    """Project view controller class."""

    def __init__(self, view: ProjectViewWindow, async_runner: QtAsyncRunner):
        self._view = view
        self._async_runner = async_runner
        self._connect_signals()
        
    def _connect_signals(self):
        pass
