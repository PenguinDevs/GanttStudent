"""
task_edit.py
Projects navigation module.
@jasonyi
Created 12/06/2024
"""

import os
from datetime import datetime, timedelta, timezone

from PyQt6.QtCore import Qt
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
    """Project view class."""
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\task_edit_window.ui")

    def __init__(self, parent: QWidget) -> None:
        """Class initialisation."""
        self._parent = parent
        super().__init__(parent)
        self._load_ui()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

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

    def reset(self, task_type: str = "task", task_data: dict = None) -> None:
        """
        Reset the controller.

        Optionally set the task data.

        Args:
            task_type (str): The type of task to edit.
            task_data (dict): The task data to edit.
        """

        # Set the task data (if any), for editing purposes. See in
        # ._on_confirm_clicked().
        self._task_data = task_data

        # Update task depending on task type.
        self.task_type = task_type
        if self.task_type == "task":
            if self._task_data:
                self._view.setWindowTitle("Edit task")
            else:
                self._view.setWindowTitle("New task")
            self._view.name_label.setText("Task:")
            self._view.end_label.show()
            self._view.end_field.show()
            self._view.completed_radio.show()
            self._view.incomplete_radio.show()
            self._view.completed_label.show()
        elif self.task_type == "milestone":
            if self._task_data:
                self._view.setWindowTitle("Edit milestone")
            else:
                self._view.setWindowTitle("New milestone")
            self._view.name_label.setText("Milestone:")
            self._view.end_label.hide()
            self._view.end_field.hide()
            self._view.completed_radio.hide()
            self._view.incomplete_radio.hide()
            self._view.completed_label.hide()

        # Set the initial fields of the task edit window.
        if task_data:
            # Set task data.
            # (Editing task).
            self.colour = task_data["colour"]
            self.start_date = task_data["start_date"]
            self.end_date = task_data["end_date"]

            self._view.name_field.setText(task_data["name"])
            self._view.description_field.setText(task_data["description"])
            self._view.completed_radio.setChecked(task_data["completed"])

            self._view.delete_button.show()
        else:
            # Set default task data.
            # (Creating new task).
            self.colour = DEFAULT_COLOUR
            self.start_date = datetime(*datetime.now(timezone.utc).timetuple()[:3]).timestamp()
            self.end_date = datetime(*datetime.now(timezone.utc).timetuple()[:3]).timestamp() + timedelta(days=1).total_seconds()

            self._view.name_field.setText("")
            self._view.description_field.setText("")
            self._view.completed_radio.setChecked(False)

            self._view.delete_button.hide()

        self.colour_buttons()
        self._display_date_fields()

    def _display_date_fields(self) -> None:
        """Update the date fields in the task edit window."""
        self._view.start_field.setText(datetime.fromtimestamp(self.start_date).strftime("%d/%m/%y"))
        self._view.end_field.setText(datetime.fromtimestamp(self.end_date).strftime("%d/%m/%y"))

    def set_colour(self, colour: str = None) -> None:
        """Set the colour of the task edit window."""
        self._view.task_colour_input.setText(colour)

    def colour_buttons(self) -> None:
        """
        Colour the colour options in the buttons in the task edit window.
        
        Also highlight the selected colour.
        """
        for button in self._view.palette_buttons.findChildren(QPushButton):
            button_colour = button.property("colour")
            if self.colour == button_colour:
                # This is when the user has selected this colour.
                button.setStyleSheet(f"background-color: {button_colour}; border: 2px solid black;")
            else:
                # This is when the user has not selected this colour.
                button.setStyleSheet(f"background-color: {button_colour};")

    def _setup_endpoints(self) -> None:
        self._new_task = QNetworkRequest()
        self._new_task.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/task/new"))
        self._new_task.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        self._update_task = QNetworkRequest()
        self._update_task.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/task/update"))
        self._update_task.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        self._delete_task = QNetworkRequest()
        self._delete_task.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/task/delete"))
        self._delete_task.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
    
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
        handle_new_response_payload(self._client, payload)

        if self._view.isVisible():
            self._view.hide()
        
        # Add the new task to the project's list of tasks.
        self._client.main_window.project_view_controller._tasks[payload["task_data"]["task_uuid"]] = payload["task_data"]
        self._client.main_window.project_view_controller.render()
    
    def _on_confirm_clicked(self) -> None:
        """
        Submit the task data to the server.

        If the ._task_data is already set, update the existing task. Otherwise,
        create a new task.
        """
        if self._task_data:
            # Update the existing task data.
            self._task_data["name"] = self._view.name_field.text()
            self._task_data["description"] = self._view.description_field.toPlainText()
            self._task_data["start_date"] = self.start_date
            self._task_data["end_date"] = self.end_date
            self._task_data["completed"] = self._view.completed_radio.isChecked()
            self._task_data["colour"] = self.colour
            self.update_task(self._task_data)
            self._client.main_window.project_view_controller.render()
        else:
            # Create a new task.
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

            self.new_task(task_data)

    def _on_task_updated_response(self, reply: QNetworkReply) -> None:
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
        handle_new_response_payload(self._client, payload)

        if self._view.isVisible():
            self._view.hide()
    
    def _on_task_deleted_response(self, reply: QNetworkReply) -> None:
        """
        A callback function for when a task is deleted.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_error(reply, reply.error())
        
        reply.deleteLater()

        payload = get_json_from_reply(reply)
        handle_new_response_payload(self._client, payload)

        if self._view.isVisible():
            self._view.hide()

        self._client.main_window.project_view_controller.fetch_tasks()

    def update_task(self, task_data: dict) -> None:
        """
        Submit the task data to the server.

        Args:
            task_data (dict): The task data to submit.
        """
        reply: QNetworkReply = self._network_manager.post(
            self._update_task,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"],
                    "project_uuid": self._client.main_window.project_view_controller._project_data["_id"],
                    "task_data": task_data
                }
            )
        )
        reply.finished.connect(lambda: self._on_task_updated_response(reply))

    def delete_task(self, task_uuid: str) -> None:
        """
        Delete the task from the server.

        Args:
            task_data (dict): The task data to delete.
        """
        reply: QNetworkReply = self._network_manager.post(
            self._delete_task,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"],
                    "project_uuid": self._client.main_window.project_view_controller._project_data["_id"],
                    "task_uuid": task_uuid
                }
            )
        )
        reply.finished.connect(lambda: self._on_task_deleted_response(reply))

    def new_task(self, task_uuid: str) -> None:
        """
        Create a task to the server.

        Args:
            task_data (dict): The task data to delete.
        """
        reply: QNetworkReply = self._network_manager.put(
            self._new_task,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"],
                    "project_uuid": self._client.main_window.project_view_controller._project_data["_id"],
                    "task_data": task_uuid
                }
            )
        )
        reply.finished.connect(lambda: self._on_new_task_response(reply))

    def _prompt_calender(self, field: str) -> None:
        """
        Prompt the user to select a date from a calender.

        Args:
            field (str): The date type to set the date for. Either "start" or
                "end".
        """
        def _set_date(date: datetime):
            print('a')
            if field == "start":
                # The start date was changed.
                self.start_date = date.timestamp()

                if self.end_date <= self.start_date:
                    # Ensure the end date is always after the end date.
                    self.end_date = self.start_date + timedelta(days=1).total_seconds()
            elif field == "end":
                # The end date was changed.
                self.end_date = date.timestamp()

                if self.end_date <= self.start_date:
                    # Ensure the end date is always after the start date.
                    self.start_date = self.end_date - timedelta(days=1).total_seconds()

            if self._task_data and (datetime.fromtimestamp(self.start_date) - self._client.main_window.project_view_controller.start_date).days < self._client.main_window.project_view_controller._task_items[self._task_data["task_uuid"]].min_column:
                # The start date cannot be before the parent task's end date.
                self.start_date = self._client.main_window.project_view_controller.start_date.timestamp() + self._client.main_window.project_view_controller._task_items[self._task_data["task_uuid"]].min_column * 24 * 60 * 60
                create_message_dialog(self._view, "Error", f"Cannot have a start date that is before the parent task's end date ({datetime.fromtimestamp(self.start_date).strftime('%d/%m/%y')}).").exec()

            self._display_date_fields()

        if field == "start":
            initial_date = datetime.fromtimestamp(self.start_date)
        elif field == "end":
            initial_date = datetime.fromtimestamp(self.end_date)
        
        create_calender_dialog(self._view, _set_date, initial_date).exec()

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
        self._view.create_button.clicked.connect(self._on_confirm_clicked)
        self._view.name_field.returnPressed.connect(self._on_confirm_clicked)

        # Bind delete event.
        self._view.delete_button.clicked.connect(lambda: self.delete_task(self._task_data["task_uuid"]))

        # Bind colour options.
        self._connect_colour_signals()

        # Bind calender buttons.
        self._view.start_field.clicked.connect(lambda: self._prompt_calender("start"))
        self._view.end_field.clicked.connect(lambda: self._prompt_calender("end"))
