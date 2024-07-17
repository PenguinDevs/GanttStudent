import os

from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data


class RegisterPage(BasePage):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\register_page.ui")

class RegisterController(BaseController):
    """Registration controller class."""

    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)
        self._view.error_frame.hide()

    def _setup_endpoints(self) -> None:
        self._register_endpoint = QNetworkRequest()
        self._register_endpoint.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/user/register"))
        self._register_endpoint.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

    def display_error(self, message: str) -> None:
        """
        Visually displays error messages in the user interface.

        Args:
            message (str): The error message to display.
        """
        self._view.error_label.setText(message)
        self._view.error_frame.show()

    def _on_register_completion(self, reply: QNetworkReply) -> None:
        """
        A callback function for when a registration request is completed.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_register_error(reply, reply.error())
        
        reply.deleteLater()

        self._switch_to_login()
        
    def _handle_register_error(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """
        A callback function for handling errors that occur from the registration
        request.

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
        else:
            self.display_error(f"An unexpected error of type {error.name}. Please try again later.")

    def register(self, username: str, password: str) -> None:
        """
        Sends a registration request to the server.

        Binds the completion callback to ._on_register_completion().

        Args:
            username (str): The username to register with.
            password (str): The password to register with.
        """
        reply: QNetworkReply = self._network_manager.post(
            self._register_endpoint,
            to_json_data(
                {
                    "username": username,
                    "password": password
                }
            )
        )
        reply.finished.connect(lambda: self._on_register_completion(reply))

    def _on_register(self) -> None:
        """
        A callback function for when the user presses the register button.
        """
        # Do not proceed if the password fields are not the same.
        if self.is_password_same() is False:
            # Display error message is already handled by ._check_password_confirmation()
            return
        elif self._view.username_field.text() == "" or self._view.password_field.text() == "":
            self.display_error("Username and password fields cannot be empty.")
            return
        elif self._view.password_confirm_field.text() == "":
            self.display_error("Password confirmation field cannot be empty.")
            return

        # Hide the error frame if it is visible.
        self._view.error_frame.hide()

        self.register(self._view.username_field.text(), self._view.password_field.text())

    def is_password_same(self) -> bool:
        """
        Check if the password and password confirmation fields are the same.

        Returns:
            bool: True if the password fields are the same, False otherwise.
        """
        return self._view.password_field.text() == self._view.password_confirm_field.text()

    def _check_password_confirmation(self) -> None:
        """
        A callback function for when the password fields are changed.

        Displays an error immediately if the password fields are not the same.
        """
        if self.is_password_same() is True:
            self._view.error_frame.hide()
        else:
            self.display_error("Passwords do not match.")
        
    def _switch_to_login(self) -> None:
        """
        Switches to the login page.
        """
        self._client.main_window.login_controller.show()

    def _connect_signals(self) -> None:
        # Bind register event.
        self._view.register_button.clicked.connect(self._on_register)
        self._view.username_field.returnPressed.connect(self._on_register)
        self._view.password_field.returnPressed.connect(self._on_register)
        self._view.password_confirm_field.returnPressed.connect(self._on_register)
        
        # Bind password confirmation check.
        self._view.password_field.textChanged.connect(self._check_password_confirmation)
        self._view.password_confirm_field.textChanged.connect(self._check_password_confirmation)

        # Set error label to wrap text.
        self._view.error_label.setWordWrap(True)

        # Switch to login screen.
        self._view.login_label.clicked.connect(self._switch_to_login)
