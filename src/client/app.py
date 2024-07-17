"""Main client application."""

from dotenv import load_dotenv

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import(
    QApplication,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget
)
from PyQt6.QtNetwork import QNetworkAccessManager

import config
from authentication.register import RegisterWindow, RegisterController
from authentication.login import LoginWindow, LoginController
# from projects.navigation import NavigationWindow, NavigationController
# from projects.view import ProjectViewWindow, ProjectViewController

load_dotenv()

class ClientApplication():
    window_size = (config.DEFAULT_WINDOW_WIDTH, config.DEFAULT_WINDOW_HEIGHT)
    is_full_screen = False

    def __init__(self) -> None:
        self.app = QApplication([])
        self.network_manager = QNetworkAccessManager()
        
        controllers = self.initialise_windows()
        
    def run(self):
        self.app.exec()

    def initialise_windows(self):
        self.register_window = RegisterWindow()
        self.register_controller = RegisterController(self, self.register_window)
        self.register_window.assign_controller(self.register_controller)
        self.register_controller.show()
        self.register_window.size()

        self.login_window = LoginWindow()
        # login_window.show()
        self.login_controller = LoginController(self, self.login_window)
        self.login_window.assign_controller(self.login_controller)

        # navigation_window = NavigationWindow()
        # # navigation_window.show()
        # navigation_controller = NavigationController(navigation_window, async_runner)

        # project_view_window = ProjectViewWindow()
        # # project_view_window.show()
        # project_view_controller = ProjectViewController(project_view_window, async_runner)

        return (
            self.register_controller,
            self.login_controller,
        )

def main():
    app = ClientApplication()
    app.run()

if __name__ == "__main__":
    main()
