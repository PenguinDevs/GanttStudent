"""Main client application."""

import os
import json
import time
from dotenv import load_dotenv

from PyQt6 import uic, QtWidgets
from PyQt6.QtWidgets import(
    QApplication,
    QMainWindow,
    QWidget
)
from PyQt6.QtNetwork import QNetworkAccessManager

from utils.window.page_base import BasePage
from utils.window.controller_base import BaseController

from authentication.register import RegisterPage, RegisterController
from authentication.login import LoginPage, LoginController
from projects.navigation import ProjectsNavigationPage, ProjectsNavigationController
from projects.view import ProjectViewPage, ProjectViewController

load_dotenv()

CACHE_PATH = "cache.json"
MIN_CACHE_SAVE_INTERVAL = 5


class ClientApplication():
    def __init__(self) -> None:
        self.app = QApplication([])
        self.network_manager = QNetworkAccessManager()

        self._setup_windows()
        self.load_cache()
        self.last_file_save = 0
        if self.cache["access_token"] is None:
            self.main_window.login_controller.show()
        else:
            self.main_window.navigation_controller.show()
    
    def load_cache(self):
        if not os.path.exists(CACHE_PATH):
            self.cache = {
                "access_token": None
            }
            self.save_cache()
            return

        with open(CACHE_PATH, "r") as file:
            self.cache = json.load(file)

    def save_cache(self):
        if time.time() - self.last_file_save < MIN_CACHE_SAVE_INTERVAL:
            return
        try:
            with open(CACHE_PATH, "w") as file:
                json.dump(self.cache, file)
                self.last_file_save = time.time()
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def switch_to(self, page: QWidget) -> None:
        return self.main_window.switch_to(page)

    def _setup_windows(self) -> None:
        self.main_window = MainWindow(self)
        self.main_window.show()

    def logout(self) -> None:
        """
        Log the user out, and return them to the login screen.
        """
        self.cache["access_token"] = None
        self.save_cache()

        # Return to login screen.
        self.main_window.login_controller.show()
    
    def exit(self):
        self.app.quit()

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

    def _initialise_page(self, page: BasePage, controller: BaseController) -> None:
        page = page()
        controller = controller(self.client, page)
        page.assign_controller(controller)
        self.stacked_widget.addWidget(page)

        return page, controller

    def _initialise_widgets(self):
        self.register_page, self.register_controller = self._initialise_page(RegisterPage, RegisterController)
        self.login_page, self.login_controller = self._initialise_page(LoginPage, LoginController)
        self.navigation_page, self.navigation_controller = self._initialise_page(ProjectsNavigationPage, ProjectsNavigationController)
        self.project_view_page, self.project_view_controller = self._initialise_page(ProjectViewPage, ProjectViewController)

        return (
            self.register_controller,
            self.login_controller,
            self.navigation_controller,
            self.project_view_controller,
        )

def main():
    app = ClientApplication()
    app.run()

if __name__ == "__main__":
    main()
