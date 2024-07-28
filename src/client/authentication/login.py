"""
login.py
Login page and controller classes.
@jasonyi
Created 23/05/2024
"""

import os

from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QCursor

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data


class LoginPage(BasePage):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\login_page.ui")

class LoginController(BaseController):
    """Login controller class."""
    
    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)
        self._view.error_frame.hide()

    def _setup_endpoints(self) -> None:
        self._login_endpoint = QNetworkRequest()
        self._login_endpoint.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/user/authorise"))
        self._login_endpoint.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

    def display_error(self, message: str) -> None:
        """
        Visually displays error messages in the user interface.

        Args:
            message (str): The error message to display.
        """
        self._view.error_label.setText(message)
        self._view.error_frame.show()

    def _on_login_completion(self, reply: QNetworkReply) -> None:
        """
        A callback function for when a login request is completed.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_login_error(reply, reply.error())
        
        response_body = get_json_from_reply(reply)
        access_token = response_body["access_token"]
        self._client.cache["access_token"] = access_token
        self._client.save_cache()

        self._client.main_window.navigation_controller.show()
        
        reply.deleteLater()
        
    def _handle_login_error(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """
        A callback function for handling errors that occur from the login request.

        Args:
            reply (QNetworkReply): The reply object from the server.
            error (QNetworkReply.NetworkError): The network error object from the
                reply.
        """
        if error is QNetworkReply.NetworkError.ContentConflictError:
            self.display_error("Username already exists. Please choose a different username.")
        elif error is QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            self.display_error(get_json_from_reply(reply)["message"])
        elif error is QNetworkReply.NetworkError.InternalServerError:
            self.display_error("The server has experienced an unexpected error.")
        elif error is QNetworkReply.NetworkError.AuthenticationRequiredError:
            self.display_error("Invalid username or password.")
        elif error is QNetworkReply.NetworkError.ContentNotFoundError:
            self.display_error("Invalid username or password.")
        else:
            self.display_error(f"An unexpected error of type {error.name}. Please try again later.")

    def login(self, username: str, password: str) -> None:
        """
        Sends a login request to the server.

        Binds the completion callback to ._on_login_completion().

        Args:
            username (str): The username to login with.
            password (str): The password to login with.
        """
        reply: QNetworkReply = self._network_manager.post(
            self._login_endpoint,
            to_json_data(
                {
                    "username": username,
                    "password": password
                }
            )
        )
        reply.finished.connect(lambda: self._on_login_completion(reply))

    def _on_login(self) -> None:
        """
        A callback function for when the user presses the login button.
        """
        if self._view.username_field.text() == "" or self._view.password_field.text() == "":
            self.display_error("Username and password fields cannot be empty.")
            return

        # Hide the error frame if it is visible.
        self._view.error_frame.hide()

        self.login(self._view.username_field.text(), self._view.password_field.text())

    def _switch_to_register(self) -> None:
        """
        Switches to the register page.
        """
        self._client.main_window.register_controller.show()

    def _connect_signals(self) -> None:
        # Bind login event.
        self._view.login_button.clicked.connect(self._on_login)
        self._view.username_field.returnPressed.connect(self._on_login)
        self._view.password_field.returnPressed.connect(self._on_login)
        
        # Set error label to wrap text.
        self._view.error_label.setWordWrap(True)


        # Switch to register screen.
        self._view.register_label.clicked.connect(self._switch_to_register)
        self._view.register_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
