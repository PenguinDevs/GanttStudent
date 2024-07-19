"""Main client application."""

import os
import json
import time
from dotenv import load_dotenv

from PyQt6 import uic
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
    """The main client application."""

    def __init__(self) -> None:
        """Class initialisation."""
        self.app = QApplication([])

        # Setup the manager to handle API calls to the server.
        self.network_manager = QNetworkAccessManager()

        # Setup the UI window.
        self._setup_window()

        # Load the user cache.
        self.load_cache()

        # When was the last time the cache was saved.
        self.last_file_save = 0

        if self.cache["access_token"] is None:
            # Show the login screen if the user is not logged in.
            self.main_window.login_controller.show()
        else:
            # Show the navigation screen if the user is logged in.
            self.main_window.navigation_controller.show()
    
    def load_cache(self):
        """
        Load the cache from the cache file.
        
        Handles the case where the cache file does not exist and creates it.
        """
        if not os.path.exists(CACHE_PATH):
            # Create the cache file if it does not exist.
            self.cache = {
                "access_token": None
            }
            self.save_cache()
            return
        else:
            # Otherwise load the cache from the file.
            with open(CACHE_PATH, "r") as file:
                self.cache = json.load(file)

    def save_cache(self):
        """
        Save the cache to the cache file.

        Only saves the cache if the last save was more than MIN_CACHE_SAVE_INTERVAL seconds ago.
        """
        if time.time() - self.last_file_save < MIN_CACHE_SAVE_INTERVAL:
            # Do not save the cache if the last save was less than MIN_CACHE_SAVE_INTERVAL seconds ago.
            return
        
        try:
            with open(CACHE_PATH, "w") as file:
                json.dump(self.cache, file)
                self.last_file_save = time.time()
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def switch_to(self, page: QWidget) -> None:
        """
        Switch to the specified page.
        
        Args:
            page (QWidget): The page to switch to.
        """
        return self.main_window.switch_to(page)

    def _setup_window(self) -> None:
        """Setup the main window for the application."""
        self.main_window = MainWindow(self)
        self.main_window.show()

    def logout(self) -> None:
        """Log the user out, and return them to the login screen."""
        self.cache["access_token"] = None
        self.save_cache()

        # Return to login screen.
        self.main_window.login_controller.show()
    
    def exit(self):
        """Exit the application."""
        self.app.quit()

    def run(self):
        """Run the application."""
        self.app.exec()

class MainWindow(QMainWindow):
    """Main UI window for the application."""

    def __init__(self, client: ClientApplication) -> None:
        """Class initialisation."""
        super().__init__()

        self.client = client

        # Load the UI elements for this base window object.
        self._load_window()

        # Initialise the pages and controllers for the application.
        self.controllers = self._initialise_widgets()
    
    def _load_window(self) -> QMainWindow:
        """
        Load the .ui file for the page, specified by self.ui_path.

        Returns:
            QMainWindow: A QMainWindow object.
        """
        return uic.load_ui.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui\\main_window.ui"), self)

    def switch_to(self, page: QWidget) -> None:
        """
        Switch to the specified page.
        
        Args:
            page (QWidget): The page to switch to.
        """
        self.stacked_widget.setCurrentWidget(page)

    def _initialise_page(self, page: BasePage, controller: BaseController) -> None:
        """
        Initialise a page and controller for the application.

        Args:
            page (BasePage): The page to initialise.
            controller (BaseController): The controller to initialise.
        """
        page = page()
        controller = controller(self.client, page)
        page.assign_controller(controller)

        # Add the page to the stacked widget so that it can be shown.
        self.stacked_widget.addWidget(page)

        return page, controller

    def _initialise_widgets(self):
        """Initialise the pages and controllers for the application."""
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
    """Runtime."""
    app = ClientApplication()
    app.run()

if __name__ == "__main__":
    main()
