import os

from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkReply
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QWidget, QMenuBar

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController
from utils.server_response import get_json_from_reply, to_json_data


class ProjectsNavigationWindow(BasePage):
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\projects_navigation_page.ui")

    def _load_ui(self) -> QWidget:
        widget = super()._load_ui()

        self.menu_bar = QMenuBar(widget)
        self.file_menu = self.menu_bar.addMenu('&File')
        self.logout_action = QAction()
        self.logout_action.setText('Log out')
        self.file_menu.addAction(self.logout_action)
        self.file_menu.addSeparator()
        self.exit_action = QAction()
        self.exit_action.setText('Exit')
        self.file_menu.addAction(self.exit_action)

        return widget
class ProjectsNavigationController(BaseController):
    """Projects navigation controller class."""
    
    def __init__(self, *args, **kwargs) -> None:
        """Class initialisation."""
        super().__init__(*args, **kwargs)

    def _setup_endpoints(self) -> None:
        self._fetch_projects_endpoint = QNetworkRequest()
        self._fetch_projects_endpoint.setUrl(QUrl(f"{os.getenv('SERVER_ADDRESS')}/user/authorise"))
        self._fetch_projects_endpoint.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

    def _on_fetch_completion(self, reply: QNetworkReply) -> None:
        """
        A callback function for when projects have been fetched.

        Args:
            reply (QNetworkReply): The reply object from the server.
        """
        # Do not proceed if there was an error.
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return self._handle_login_error(reply, reply.error())
        
        reply.deleteLater()

    def logout(self) -> None:
        self._client.cache["access_token"] = None
        self._client.save_cache()
        self._client.main_window.login_controller.show()

    def _connect_signals(self) -> None:
        self._view.logout_action.triggered.connect(self.logout)

