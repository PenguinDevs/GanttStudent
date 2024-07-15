import sys

from PyQt6.QtWidgets import(
    QApplication,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

class LoginWindow(QMainWindow):
    def __init__(self) -> None:
        pass

    def _create

def main():
    # Debugging purposes only.
    app = QApplication([])
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
