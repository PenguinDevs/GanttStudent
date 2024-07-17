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

from authentication.register import RegisterWindow, RegisterController
# from authentication.login import LoginWindow, LoginController
# from projects.navigation import NavigationWindow, NavigationController
# from projects.view import ProjectViewWindow, ProjectViewController

load_dotenv()


def initialise_windows(app: QApplication, network_manager: QNetworkAccessManager):
    register_window = RegisterWindow()
    register_window.show()
    register_controller = RegisterController(register_window, network_manager)

    # login_window = LoginWindow()
    # # login_window.show()
    # login_controller = LoginController(login_window, async_runner)

    # navigation_window = NavigationWindow()
    # # navigation_window.show()
    # navigation_controller = NavigationController(navigation_window, async_runner)

    # project_view_window = ProjectViewWindow()
    # # project_view_window.show()
    # project_view_controller = ProjectViewController(project_view_window, async_runner)

    return (
        register_window,
        # login_window,
        # navigation_window,
        # project_view_window
    ), (
        register_controller,
        # login_controller,
        # navigation_controller,
        # project_view_controller
    )

def main():
    app = QApplication([])
    network_manager = QNetworkAccessManager()
    
    windows = initialise_windows(app, network_manager)
    
    app.exec()

if __name__ == "__main__":
    main()
