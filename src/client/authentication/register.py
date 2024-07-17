import os
import json

from PyQt6.QtWidgets import(
    QMainWindow,
    
)
from PyQt6 import uic
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager, QNetworkReply
from PyQt6.QtCore import QUrl

import config
from utils.server_response import get_json_from_reply, to_json_data


class RegisterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._load_ui()
        self._assign_window_properties()

    def _load_ui(self):
        return uic.load_ui.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\register_window.ui"), self)

    def _assign_window_properties(self):
        self.username_field = self.username_field
        self.password_field = self.password_field
        self.password_confirm_field = self.password_confirm_field
        self.register_button = self.register_button

        self.login_text = self.login_text

        self.error_frame = self.error_frame
        self.error_label = self.error_label

class RegisterController:
    """Register controller class."""

    def __init__(self, view: RegisterWindow, network_manager: QNetworkAccessManager):
        self._view = view
        self._network_manager = network_manager
        self._connect_signals()
        self._setup_endpoints()
        self._view.error_frame.hide()

    def _setup_endpoints(self):
        self._register_endpoint = QNetworkRequest()
        self._register_endpoint.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/user/register"))
        self._register_endpoint.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

    def display_error(self, message: str):
        self._view.error_label.setText(message)
        self._view.error_frame.show()

    def _on_register_completion(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_register_error(reply, reply.error())
        
        print("Register completed", get_json_from_reply(reply))
        
        reply.deleteLater()
        
    def _handle_register_error(self, reply: QNetworkReply, error: QNetworkReply.NetworkError):
        if error is QNetworkReply.NetworkError.ContentConflictError:
            self.display_error("Username already exists. Please choose a different username.")
        elif error is QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            self.display_error(get_json_from_reply(reply)["message"])
        elif error is QNetworkReply.NetworkError.InternalServerError:
            self.display_error("The server has experienced an unexpected error.")
        else:
            self.display_error(f"An unexpected error of type {error.name}. Please try again later.")

    def register(self, username: str, password: str):
        reply: QNetworkReply = self._network_manager.post(
            self._register_endpoint,
            to_json_data(
                {
                    "username": username,
                    "password": password
                }
            )
        )
        # reply.errorOccurred.connect(lambda error: self._handle_register_error(reply, error))
        reply.finished.connect(lambda: self._on_register_completion(reply))

    def _on_register(self):
        if self.is_password_same() is False:
            # Display error message is already handled by ._check_password_confirmation()
            return

        self._view.error_frame.hide()
        self.register(self._view.username_field.text(), self._view.password_field.text())

    def is_password_same(self):
        return self._view.password_field.text() == self._view.password_confirm_field.text()

    def _check_password_confirmation(self):
        if self.is_password_same() is True:
            self._view.error_frame.hide()
        else:
            self.display_error("Passwords do not match.")
        
    def _connect_signals(self):
        self._view.register_button.clicked.connect(self._on_register)
        self._view.username_field.returnPressed.connect(self._on_register)
        self._view.password_field.returnPressed.connect(self._on_register)
        self._view.password_confirm_field.returnPressed.connect(self._on_register)
        
        self._view.password_field.textChanged.connect(self._check_password_confirmation)
        self._view.password_confirm_field.textChanged.connect(self._check_password_confirmation)

        self._view.error_label.setWordWrap(True)
