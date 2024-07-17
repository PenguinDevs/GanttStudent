from PyQt6.QtWidgets import(
    QWidget,
    QDialog,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
)

def create_message_dialog(parent: QWidget, title: str, message: str, button_message: str = 'Ok') -> QDialog:
    """
    Create a message dialog with a title, message, and a single button.

    Args:
        parent (QWidget):  The parent widget for the dialog.
        title (str): The title of the dialog.
        message (str): The message to display in the dialog.
        button_message (str, optional): The message to display in the
            button. Defaults to 'Ok'.

    Returns:
        QDialog: _description_
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)

    # Create ui elements with a message.
    label = QLabel(message)
    button = QPushButton(button_message)

    # Create a layout for the dialog.
    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(label)
    dialog_layout.addWidget(button)

    dialog.setLayout(dialog_layout)

    # Bind the button to close the dialog.
    button.clicked.connect(dialog.close)
    
    return dialog

def create_text_input_dialog(parent: QWidget, callback, title: str, placeholder: str = '', button_message: str = 'Confirm') -> QDialog:
    """
    Create a text input dialog with a title, text placeholder, and a
    confirmation button.

    Args:
        parent (QWidget):  The parent widget for the dialog.
        callback (function): The function to call when the dialog is
            confirmed.
        title (str): The title of the dialog.
        placeholder (str): The message to display as a placeholder.
        button_message (str, optional): The message to display in the
            button. Defaults to 'Confirm'.

    Returns:
        QDialog: _description_
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)

    # Create ui elements with a message.
    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder)
    button = QPushButton(button_message)

    # Create a layout for the dialog.
    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(line_edit)
    dialog_layout.addWidget(button)

    dialog.setLayout(dialog_layout)

    def close_dialog():
        callback(line_edit.text())
        dialog.close()

    # Bind the button to close the dialog.
    line_edit.returnPressed.connect(close_dialog)
    button.clicked.connect(close_dialog)
    
    return dialog
