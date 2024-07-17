import os

from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl

from utils.window.window_base import BaseWindow
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data


class LoginWindow(BaseWindow):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\login_window.ui")

    def _assign_window_properties(self):
        self.username_field = self.username_field
        self.password_field = self.password_field
        self.login_button = self.login_button

        self.register_label = self.register_label

        self.error_frame = self.error_frame
        self.error_label = self.error_label

class LoginController(BaseController):
    """Login controller class."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._view.error_frame.hide()

    def _setup_endpoints(self):
        self._login_endpoint = QNetworkRequest()
        self._login_endpoint.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/user/login"))
        self._login_endpoint.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

    def display_error(self, message: str):
        self._view.error_label.setText(message)
        self._view.error_frame.show()

    def _on_login_completion(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_login_error(reply, reply.error())
        
        print("Register completed", get_json_from_reply(reply))
        
        reply.deleteLater()
        
    def _handle_login_error(self, reply: QNetworkReply, error: QNetworkReply.NetworkError):
        if error is QNetworkReply.NetworkError.ContentConflictError:
            self.display_error("Username already exists. Please choose a different username.")
        elif error is QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            self.display_error(get_json_from_reply(reply)["message"])
        elif error is QNetworkReply.NetworkError.InternalServerError:
            self.display_error("The server has experienced an unexpected error.")
        else:
            self.display_error(f"An unexpected error of type {error.name}. Please try again later.")

    def login(self, username: str, password: str):
        reply: QNetworkReply = self._network_manager.post(
            self._login_endpoint,
            to_json_data(
                {
                    "username": username,
                    "password": password
                }
            )
        )
        # reply.errorOccurred.connect(lambda error: self._handle_register_error(reply, error))
        reply.finished.connect(lambda: self._on_login_completion(reply))

    def _on_login(self):
        self._view.error_frame.hide()
        self.login(self._view.username_field.text(), self._view.password_field.text())

    def _switch_to_register(self):
        self._view.hide()
        self._client.register_controller.show()

    def _connect_signals(self):
        self._view.login_button.clicked.connect(self._on_login)
        self._view.username_field.returnPressed.connect(self._on_login)
        self._view.password_field.returnPressed.connect(self._on_login)
        
        self._view.error_label.setWordWrap(True)

        self._view.register_label.clicked.connect(self._switch_to_register)
