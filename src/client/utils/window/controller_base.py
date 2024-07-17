from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6 import QtCore

if TYPE_CHECKING:
    from utils.window.window_base import BaseWindow
    from app import ClientApplication


class BaseController():
    def __init__(self, client: ClientApplication, view: BaseWindow):
        self._view = view
        self._client = client
        self._network_manager = client.network_manager
        self._setup_endpoints()
        self._connect_signals()

    def _setup_endpoints(self):
        raise NotImplementedError()
    
    def _connect_signals(self):
        raise NotImplementedError()

    def show(self):
        if self._client.is_full_screen:
            self._view.showMaximized()
        else:
            self._view.resize(self._client.window_size[0], self._client.window_size[1])
            self._view.showNormal()
        self._view.show()

    def hide(self):
        self._view.hide()

    def on_resize(self, size: QtCore.QSize):
        self._client.window_size = (size.width(), size.height())

    def on_window_state_change(self, is_full_screen: bool):
        self._client.is_full_screen = is_full_screen
