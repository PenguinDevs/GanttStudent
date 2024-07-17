from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMainWindow
from PyQt6 import uic, QtCore, QtGui

if TYPE_CHECKING:
    from utils.window.controller_base import BaseController

class BaseWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._load_ui()
        self._assign_window_properties()

    def _load_ui(self):
        return uic.load_ui.loadUi(self.ui_path, self)
    
    def _assign_window_properties(self):
        raise NotImplementedError()
    
    def assign_controller(self, controller: BaseController):
        self._controller = controller

    def resizeEvent(self, event: QtGui.QResizeEvent):
        self._controller.on_resize(event.size())

    def changeEvent(self, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            self._controller.on_window_state_change(self.isMaximized())
