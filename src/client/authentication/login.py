import os

from PyQt6.QtWidgets import(
    QMainWindow,
    
)
from PyQt6 import uic


class LoginWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._load_ui()
        self._assign_window_properties()

    def _load_ui(self):
        return uic.load_ui.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\login_window.ui"), self)

    def _assign_window_properties(self):
        self.username_field = self.username_field
        self.password_field = self.password_field
        self.login_button = self.login_button

        self.register_text = self.register_text

        self.error_frame = self.error_frame
        self.error_label = self.error_label
class LoginController:
    """Authentication controller class."""

    def __init__(self, view: LoginWindow, async_runner: QtAsyncRunner):
        self._view = view
        self._async_runner = async_runner
        self._connect_signals()

    def display_error(self, message: str):
        self._view.error_label.setText(message)
        self._view.error_frame.show()

    async def login(self, username: str, password: str):
        print(username, password)

    async def _on_login(self, checked: bool):
        self._view.error_frame.hide()
        
    def _connect_signals(self):
        self._view.login_button.clicked.connect(self._async_runner.to_sync(self._on_login))
        self._view.username_field.returnPressed.connect(self._async_runner.to_sync(self._on_login))
        self._view.password_field.returnPressed.connect(self._async_runner.to_sync(self._on_login))
        
        self._view.error_label.setWordWrap(True)
