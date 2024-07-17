"""Main client application."""

import os
from dotenv import load_dotenv

from PyQt6 import uic, QtWidgets
from PyQt6.QtWidgets import(
    QApplication,
    QMainWindow,
    QWidget
)
from PyQt6.QtNetwork import QNetworkAccessManager

import config
from authentication.register import RegisterPage, RegisterController
from authentication.login import LoginWindow, LoginController
# from projects.navigation import NavigationWindow, NavigationController
# from projects.view import ProjectViewWindow, ProjectViewController

load_dotenv()


class ClientApplication():
    def __init__(self) -> None:
        self.app = QApplication([])
        self.network_manager = QNetworkAccessManager()

        self._setup_windows()

    def switch_to(self, page: QWidget) -> None:
        return self.main_window.switch_to(page)

    def _setup_windows(self):
        self.main_window = MainWindow(self)
        self.main_window.show()
        
    def run(self):
        self.app.exec()

class MainWindow(QMainWindow):
    def __init__(self, client: ClientApplication) -> None:
        super().__init__()

        self.client = client

        self._load_window()
        self.controllers = self._initialise_widgets()
    
    def _load_window(self) -> QMainWindow:
        """
        Load the .ui file for the page, specified by self.ui_path.

        Returns:
            QMainWindow: A QMainWindow object.
        """
        return uic.load_ui.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\main_window.ui"), self)

    def switch_to(self, page: QWidget) -> None:
        self.stacked_widget.setCurrentWidget(page)

    def _initialise_widgets(self):
        self.register_page = RegisterPage()
        self.register_controller = RegisterController(self.client, self.register_page)
        self.register_page.assign_controller(self.register_controller)
        self.stacked_widget.addWidget(self.register_page)

        self.login_page = LoginWindow()
        # login_window.show()
        self.login_controller = LoginController(self.client, self.login_page)
        self.login_page.assign_controller(self.login_controller)
        self.stacked_widget.addWidget(self.login_page)

        # navigation_window = NavigationWindow()
        # # navigation_window.show()
        # navigation_controller = NavigationController(navigation_window, async_runner)

        # project_view_window = ProjectViewWindow()
        # # project_view_window.show()
        # project_view_controller = ProjectViewController(project_view_window, async_runner)

        return (
            self.register_controller,
            # self.login_controller,
        )

def main():
    app = ClientApplication()
    app.run()

if __name__ == "__main__":
    main()
