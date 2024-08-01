"""
navigation/__init__.py
Projects navigation module.
@jasonyi
Created 30/05/2024
"""

import os
import json

from PyQt6 import uic
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QAction, QImage, QPixmap
from PyQt6.QtWidgets import QWidget, QMenuBar, QGridLayout

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data, handle_new_response_payload
from utils.dialog import create_message_dialog, create_text_input_dialog

from projects.view.export import export_project

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_projects")
MAX_PROJECTS_COLUMNS = 3


class ProjectsNavigationPage(BasePage):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\projects_navigation_page.ui")

    def _load_ui(self) -> QWidget:
        widget = super()._load_ui()

        self.menu_bar = QMenuBar(widget)
        
        self.file_menu = self.menu_bar.addMenu('&File')

        self.logout_action = QAction()
        self.logout_action.setText('Log out')
        self.file_menu.addAction(self.logout_action)
        
        self.exit_action = QAction()
        self.exit_action.setText('Exit')
        self.file_menu.addAction(self.exit_action)

        return widget
class ProjectsNavigationController(BaseController):
    """Projects navigation controller class."""
    
    # Search query
    query = ''

    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

        self.projects = {}

    def _setup_endpoints(self) -> None:
        self._new_project = QNetworkRequest()
        self._new_project.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/new-project"))
        self._new_project.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        self._delete_project = QNetworkRequest()
        self._delete_project.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/delete-project"))
        self._delete_project.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        self._fetch_projects_endpoint = QNetworkRequest()
        self._fetch_projects_endpoint.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/fetch-user-projects"))
        self._fetch_projects_endpoint.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        self._rename_project = QNetworkRequest()
        self._rename_project.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/project/rename-project"))
        self._rename_project.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

    def _on_rename_project_response(self, reply: QNetworkReply) -> None:
        """
        A callback function for when a project is renamed.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_error(reply, reply.error())
        
        reply.deleteLater()

        payload = get_json_from_reply(reply)
        handle_new_response_payload(self._client, payload)
        self.fetch_projects()

    def rename_project(self, uuid: str, new_name: str) -> None:
        """
        Rename a project.

        Args:
            uuid (str): The uuid of the project.
            new_name (str): The new name of the project.
        """
        reply: QNetworkReply = self._network_manager.post(
            self._rename_project,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"],
                    "uuid": uuid,
                    "name": new_name,
                }
            )
        )
        reply.finished.connect(lambda: self._on_rename_project_response(reply))

    def _on_delete_project_response(self, reply: QNetworkReply) -> None:
        """
        A callback function for when a project is deleted.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_error(reply, reply.error())
        
        reply.deleteLater()

        payload = get_json_from_reply(reply)
        handle_new_response_payload(self._client, payload)
        self.fetch_projects()

    def delete_project(self, uuid: str) -> None:
        """
        Delete a project from the server.

        Args:
            uuid (str): The uuid of the project to delete.
        """
        reply: QNetworkReply = self._network_manager.post(
            self._delete_project,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"],
                    "uuid": uuid,
                }
            )
        )
        reply.finished.connect(lambda: self._on_delete_project_response(reply))

    def render_projects(self) -> None:
        """
        Render the projects on the screen.

        Takes into account of what the .query attribute is set to, and displays
        the relevant projects accordingly.
        """
        projects = self.projects.copy()
        omitted = []
        for uuid, project_data in projects.items():
            if self.query.lower() not in project_data["name"].lower():
                omitted.append(uuid)
        for uuid in omitted:
            projects.pop(uuid)
            item = self._view.scroll_body.findChild(QWidget, uuid)
            if item:
                self._view.scroll_body.layout().removeWidget(item)
                item.deleteLater()
        
        sorted_projects = sorted(projects.items(), key=lambda x: x[1]["updated_at"], reverse=True)

        layout: QGridLayout = self._view.scroll_body.layout()
        for i, (uuid, project_data) in enumerate(sorted_projects):
            row, column = divmod(i, MAX_PROJECTS_COLUMNS)
            item = self._view.scroll_body.findChild(QWidget, uuid)
            if item:
                layout.removeWidget(item)
                layout.addWidget(item, row, column)
                item.show()
                continue
                
            item = ProjectViewItem(self, project_data["name"], project_data["_id"])
            layout.setRowMinimumHeight(row, 300)
            layout.addWidget(item, row, column)

    def _reconciliate_projects(self, server_projects: dict) -> None:
        """
        Deletes any projects that are missing from the server on the local
        machine.

        Creates any new projects that are on the server but not on the local
        machine.

        Finally, calls the .render_projects() method to render the projects on
        the screen.

        Args:
            server_projects (dict): A dictionary of projects from the server.
        """
        server_projects = server_projects or {}
        self.projects = {}
        
        for file in os.listdir(PROJECTS_DIR):
            if not file.endswith(".json"):
                print(f"Skipping {file}")
                continue

            with open(os.path.join(PROJECTS_DIR, file), "r") as f:
                project_data = json.load(f)
                self.projects[project_data["_id"]] = project_data

        deleted = []
        for uuid, project_data in self.projects.items():
            if not uuid in server_projects.keys():
                try:
                    os.remove(os.path.join(PROJECTS_DIR, f"{uuid}.json"))
                except:
                    print(f"Failed to delete {uuid}")

                item = self._view.scroll_body.findChild(QWidget, uuid)
                if item:
                    self._view.scroll_body.layout().removeWidget(item)
                    item.deleteLater()
            
                deleted.append(uuid)
        
        for uuid in deleted:
            self.projects.pop(uuid)

        for uuid, project_data in server_projects.items():
            with open(os.path.join(PROJECTS_DIR, f"{uuid}.json"), "w") as f:
                json.dump(project_data, f, indent=4)
            self.projects[uuid] = project_data

        self.render_projects()

    def _on_fetch_completion(self, reply: QNetworkReply) -> None:
        """
        A callback function for when projects have been fetched.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_error(reply, reply.error())
        
        reply.deleteLater()

        payload = get_json_from_reply(reply)
        handle_new_response_payload(self._client, payload)
        self._reconciliate_projects(payload["projects"])
        
    def fetch_projects(self) -> None:
        """
        Fetch all projects from the server that the user has access to.
        """
        reply: QNetworkReply = self._network_manager.post(
            self._fetch_projects_endpoint,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"]
                }
            )
        )
        reply.finished.connect(lambda: self._on_fetch_completion(reply))

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
            create_message_dialog(self._view, "Error", "The project could not be found.").exec()
        else:
            create_message_dialog(self._view, "Error", "An error occurred. Please try again.").exec()
        
        self.fetch_projects()

    def _on_new_project_response(self, reply: QNetworkReply) -> None:
        """
        A callback function for when a new project request is sent.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_error(reply, reply.error())
        
        reply.deleteLater()

        payload = get_json_from_reply(reply)
        handle_new_response_payload(self._client, payload)
        self.fetch_projects()

    def new_project(self, project_name: str) -> None:
        reply: QNetworkReply = self._network_manager.put(
            self._new_project,
            to_json_data(
                {
                    "access_token": self._client.cache["access_token"],
                    "project_name": project_name.strip(),
                }
            )
        )
        reply.finished.connect(lambda: self._on_new_project_response(reply))

    def _on_create_project(self) -> None:
        """
        A callback function for a new project button is clicked.
        """
        create_text_input_dialog(self._view, self.new_project, "Create a new project", "Enter the name of the project").exec()

    def _on_search_query(self) -> None:
        """
        A callback function for when a search query is changed.
        """
        self.query = self._view.search_field.text()
        self.render_projects()

    def reset(self) -> None:
        """
        Reset the controller.
        """
        self.projects = {}
        self.query = ''

        layout: QGridLayout = self._view.scroll_body.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item:
                widget = item.widget()
                widget.deleteLater()

    def show(self) -> None:
        """
        Show the projects navigation screen.

        Also fetches the projects from the server by doing so.
        """
        super().show()
        self.reset()
        self.fetch_projects()

    def _connect_signals(self) -> None:
        # Bind menu bar actions.
        self._view.logout_action.triggered.connect(self._client.logout)
        self._view.exit_action.triggered.connect(self._client.exit)

        # Bind new project button.
        self._view.new_project_button.clicked.connect(self._on_create_project)

        # Bind search field updated.
        self._view.search_field.textChanged.connect(self._on_search_query)

class ProjectViewItem(QWidget):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\project_view_item.ui")

    def __init__(self, controller: ProjectsNavigationController, name: str, uuid: str) -> None:
        self._controller = controller
        super().__init__(controller._view)
        self._load_ui(name, uuid)

    def open(self) -> None:
        """
        Open this project
        """
        self._controller._client.main_window.project_view_controller.show()
        self._controller._client.main_window.project_view_controller.load(self._controller.projects[self.objectName()])

    def delete(self) -> None:
        """
        Delete this project.
        """
        self._controller.delete_project(self.objectName())

    def rename(self) -> None:
        """
        Rename this project, to the name given by the input in the .item_name
        field.
        """
        self.item_name.clearFocus()
        if self.item_name.text() == self._controller.projects[self.objectName()]["name"]:
            return
        
        self._controller.rename_project(self.objectName(), self.item_name.text())

    def _load_ui(self, name: str, uuid: str) -> QWidget:
        """
        Load the UI for the project view item.

        Args:
            name (str): The name of the project.
            uuid (str): The uuid of the project.

        Returns:
            QWidget: The widget object created.
        """
        widget = uic.load_ui.loadUi(self.ui_path, self)
        widget.setObjectName(uuid)
        widget.item_name.setText(name)

        # Bind open events.
        widget.open_button.clicked.connect(self.open)

        # Bind delete events.
        widget.delete_button.clicked.connect(self.delete)

        # Bind rename events.
        widget.item_name.returnPressed.connect(self.rename)
        widget.item_name.focusOutEvent = lambda event: self.rename()

        # Set preview image.
        def on_tasks_fetched(reply: QNetworkReply) -> None:
            # Do not proceed if there was an error.
            if reply.error() != QNetworkReply.NetworkError.NoError:
                return self._controller._handle_error(reply, reply.error())
            
            reply.deleteLater()

            payload = get_json_from_reply(reply)
            handle_new_response_payload(self._controller._client, payload)

            image = export_project(self._controller.projects[uuid], payload["tasks"])

            data = image.tobytes("raw", "RGB") 
            q_image = QImage(data, image.size[0], image.size[1], image.size[0]*3, QImage.Format.Format_RGB888)
            q_pixmap = QPixmap.fromImage(q_image)
            widget.image_preview.setPixmap(q_pixmap)
            widget.image_preview.setScaledContents(True)

        self._controller._client.main_window.project_view_controller.fetch_tasks(uuid, on_tasks_fetched)

        return widget
