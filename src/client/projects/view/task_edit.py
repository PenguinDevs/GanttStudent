"""Projects navigation module."""

import os
import json

from PyQt6 import uic
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QMainWindow, QPushButton

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data, handle_new_response_payload
from utils.dialog import create_message_dialog, create_text_input_dialog

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_projects")
MAX_PROJECTS_COLUMNS = 3


class TaskEditWindow(QMainWindow):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\task_edit_window.ui")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._load_ui()

    def _load_ui(self) -> QWidget:
        """
        Load the .ui file for the page, specified by self.ui_path.

        Returns:
            QWidget: A QMainWindow object.
        """
        return uic.load_ui.loadUi(self.ui_path, self)

class TaskEditController(BaseController):
    """Project view controller class."""

    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)
        self.colour_buttons()

    def colour_buttons(self) -> None:
        
        for button in self._view.palette_buttons.findChildren(QPushButton):
            button.setStyleSheet(f"background-color: {button.property('colour')};")
            # button.clicked.connect(self._set_palette)

    def _setup_endpoints(self) -> None:
        self._new_task = QNetworkRequest()
        self._new_task.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/edit/task/new-task"))
        self._new_task.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
    
    def _handle_error(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """
        A callback function for handling errors that occur from any of the
        endpoints in this controller.

        Args:
            reply (QNetworkReply): The reply object from the server.
            error (QNetworkReply.NetworkError): The network error object from the
                reply.
        """
        if error is QNetworkReply.NetworkError.ContentGoneError:
            self.logout()
            create_message_dialog(self._view, "Session expired", "Your session has expired. Please log in again.").exec()
            return
        elif error is QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            create_message_dialog(self._view, "Error", get_json_from_reply(reply)["message"]).exec()
        elif error is QNetworkReply.NetworkError.ContentNotFoundError:
            create_message_dialog(self._view, "Error", "The project could not be found.").exec()
        else:
            create_message_dialog(self._view, "Error", "An error occurred. Please try again.").exec()
        
        self.fetch_projects()

    def _connect_signals(self) -> None:
        pass
