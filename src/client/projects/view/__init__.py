"""Projects navigation module."""

import os
import json

from PyQt6 import uic
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget, QMenuBar

from .task_edit import TaskEditWindow, TaskEditController

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data, handle_new_response_payload
from utils.dialog import create_message_dialog, create_text_input_dialog

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_projects")
MAX_PROJECTS_COLUMNS = 3


class ProjectViewPage(BasePage):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\project_view_page.ui")

    def _load_ui(self) -> QWidget:
        widget = super()._load_ui()

        self.menu_bar = QMenuBar(widget)

        self.file_menu = self.menu_bar.addMenu('&File')

        self.close_action = QAction()
        self.close_action.setText('Close')
        self.file_menu.addAction(self.close_action)

        self.file_menu.addSeparator()

        self.logout_action = QAction()
        self.logout_action.setText('Log out')
        self.file_menu.addAction(self.logout_action)

        self.exit_action = QAction()
        self.exit_action.setText('Exit')
        self.file_menu.addAction(self.exit_action)

        self.edit_menu = self.menu_bar.addMenu('&Edit')

        self.undo_action = QAction()
        self.undo_action.setText('Undo')
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QAction()
        self.redo_action.setText('Redo')
        self.edit_menu.addAction(self.redo_action)

        self.edit_menu.addSeparator()

        self.create_menu = self.edit_menu.addMenu('&Create')

        self.new_task_action = QAction()
        self.new_task_action.setText('New task')
        self.create_menu.addAction(self.new_task_action)

        self.new_milestone_action = QAction()
        self.new_milestone_action.setText('New milestone')
        self.create_menu.addAction(self.new_milestone_action)

        return widget
class ProjectViewController(BaseController):
    """Project view controller class."""

    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

        self.task_edit_window = TaskEditWindow(self._view)
        self.task_edit_controller = TaskEditController(self._client, self.task_edit_window)

        self._tasks = {}
        self._milestones = {}

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

    def _create_task_object(self, task_data: dict) -> None:
        """
        Create a task object from the task data.

        Args:
            task_data (dict): The task data to create the task object from.
        """
        self.task_edit_window.show()

    def create_task(self) -> None:
        """
        Create a new task.
        """
        self.task_edit_window.show()

    def create_milestone(self) -> None:
        """
        Create a new milestone.
        """
        self.task_edit_window.show()

    def reset(self) -> None:
        """
        Reset the controller.
        """
        self._project_data = None

    def load(self, project_data: dict) -> None:
        """
        Load the projects for the user.

        Args:
            project_data (dict): The project data to load.
        """
        self._project_data = project_data

        self._view.title.setText(project_data["name"])

    def close(self) -> None:
        """
        Close the project view.
        """
        self._client.main_window.navigation_controller.show()
        self.reset()

    def _connect_signals(self) -> None:
        # Bind menu bar actions.
        self._view.logout_action.triggered.connect(self._client.logout)
        self._view.exit_action.triggered.connect(self._client.exit)

        # Bind back button.
        self._view.back_button.clicked.connect(self.close)
        self._view.close_action.triggered.connect(self.close)

        # Bind task/milestone creation events.
        self._view.new_task_action.triggered.connect(self.create_task)
        self._view.new_milestone_action.triggered.connect(self.create_milestone)
        self._view.add_task_button.clicked.connect(self.create_task)
        self._view.add_milestone_button.clicked.connect(self.create_milestone)
