"""Projects navigation module."""

import os
from datetime import datetime, timedelta, timezone

from PyQt6 import uic
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QMainWindow, QPushButton

from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data, handle_new_response_payload
from utils.dialog import create_message_dialog, create_calender_dialog

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_projects")
MAX_PROJECTS_COLUMNS = 3
DEFAULT_COLOUR = "#ffffff"


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
        self.reset()

    def reset(
            self,
            task_type: str = "task",
            colour: str = None,
            start_date: int = None,
            end_date: int = None,
            name: str = None,
            description: str = None,
            completed: bool = None,
    ) -> None:
        self.task_type = task_type
        if task_type == "task":
            self._view.setWindowTitle("Edit task")
            self._view.name_label.setText("Task:")
        elif task_type == "milestone":
            self._view.setWindowTitle("Edit milestone")
            self._view.name_label.setText("Milestone:")

        self.colour = colour or DEFAULT_COLOUR
        self.start_date = start_date or datetime(*datetime.now(timezone.utc).timetuple()[:3]).timestamp()
        self.end_date = end_date or datetime(*datetime.now(timezone.utc).timetuple()[:3]).timestamp() + timedelta(days=1).total_seconds()

        self._view.name_field.setText(name or "")
        self._view.description_field.setText(description or "")
        self._view.completed_radio.setChecked(False if completed is None else completed)

        self.colour_buttons()
        self._display_date_fields()

    def _display_date_fields(self) -> None:
        self._view.start_field.setText(datetime.fromtimestamp(self.start_date).strftime("%d/%m/%y"))
        self._view.end_field.setText(datetime.fromtimestamp(self.end_date).strftime("%d/%m/%y"))

    def set_colour(self, colour: str = None) -> None:
        self._view.task_colour_input.setText(colour)

    def colour_buttons(self) -> None:
        for button in self._view.palette_buttons.findChildren(QPushButton):
            button_colour = button.property('colour')
            if self.colour == button_colour:
                button.setStyleSheet(f"background-color: {button_colour}; border: 2px solid black;")
            else:
                button.setStyleSheet(f"background-color: {button_colour};")

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
            self._client.logout()
            create_message_dialog(self._view, "Session expired", "Your session has expired. Please log in again.").exec()
            return
        elif error is QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            create_message_dialog(self._view, "Error", get_json_from_reply(reply)["message"]).exec()
        elif error is QNetworkReply.NetworkError.ContentNotFoundError:
            create_message_dialog(self._view, "Error", "The task could not be found.").exec()
        else:
            create_message_dialog(self._view, "Error", "An error occurred. Please try again.").exec()

    def _prompt_calender(self, field: str) -> None:
        def _set_date(date: datetime):
            if field == "start":
                self.start_date = date.timestamp()
            elif field == "end":
                self.end_date = date.timestamp()

            self._display_date_fields()

        if field == "start":
            initial_date = datetime.fromtimestamp(self.start_date)
        elif field == "end":
            initial_date = datetime.fromtimestamp(self.end_date)
        
        create_calender_dialog(self._view, _set_date, initial_date).exec()

    def _on_new_task_response(self, reply: QNetworkReply) -> None:
        """
        A callback function for when a new task is added.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_error(reply, reply.error())
        
        reply.deleteLater()

        payload = get_json_from_reply(reply)
        print(payload)
        handle_new_response_payload(self._client, payload)
    
    def _submit_task(self, task_data: dict) -> None:
        """
        Submit the task data to the server.

        Args:
            task_data (dict): The task data to submit.
        """
        task_data = {
            "task_type": self.task_type,
            "name": self._view.name_field.text(),
            "description": self._view.description_field.toPlainText(),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "completed": self._view.completed_radio.isChecked(),
            "colour": self.colour,
            "dependencies": [],
        }

        reply: QNetworkReply = self._network_manager.put(
            self._new_task,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"],
                    "project_uuid": self._client.main_window.project_view_controller._project_data["_id"],
                    "task_data": task_data
                }
            )
        )
        reply.finished.connect(lambda: self._on_new_task_response(reply))

    def _connect_colour_signals(self) -> None:
        def _button_callback(colour: str):
            self.colour = colour

            def set_colour():
                self.colour = colour
                self.colour_buttons()

            return set_colour

        for button in self._view.palette_buttons.findChildren(QPushButton):
            button.clicked.connect(_button_callback(button.property("colour")))

    def _connect_signals(self) -> None:
        # Bind cancel event.
        self._view.cancel_button.clicked.connect(self._view.hide)

        # Bind create event.
        self._view.create_button.clicked.connect(self._submit_task)

        # Bind colour options.
        self._connect_colour_signals()

        # Bind calender buttons.
        self._view.start_field.clicked.connect(lambda: self._prompt_calender("start"))
        self._view.end_field.clicked.connect(lambda: self._prompt_calender("end"))
