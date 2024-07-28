"""
dialog.py
Dialog popups for the client application.
@jasonyi
Created 28/05/2024
"""
from datetime import datetime

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import(
    QWidget,
    QDialog,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QCalendarWidget,
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

def create_calender_dialog(parent: QWidget, callback, initial_date: datetime) -> QDialog:
    """
    Create a calender dialog for selecting a date.

    Args:
        parent (QWidget): The parent widget for the dialog.
        callback (function): The function to call when a date is selected.

    Returns:
        QDialog: The calender dialog.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Select a date")

    # Convert the initial date to a QDate object.
    initial_date_qdate = QDate()
    initial_date_qdate.setDate(initial_date.year, initial_date.month, initial_date.day)

    # Create a calender widget.
    calender = QCalendarWidget()
    calender.setSelectedDate(initial_date_qdate)

    # Create buttons.
    confirm_button = QPushButton("Confirm")
    cancel_button = QPushButton("Cancel")

    # Create a layout for the dialog.
    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(calender)
    dialog_layout.addWidget(confirm_button)
    dialog_layout.addWidget(cancel_button)

    dialog.setLayout(dialog_layout)

    def close_dialog(override_date: datetime = None):
        if override_date is None:
            selected_date = calender.selectedDate()
            try:
                if selected_date.year() > 3000:
                    raise ValueError
                callback(datetime(selected_date.year(), selected_date.month(), selected_date.day()))
            except ValueError:
                # Invalid date given
                callback(initial_date)
        else:
            callback(override_date)
        dialog.close()

    # Bind the button to close the dialog.
    # Return the new date if confirmed.
    confirm_button.clicked.connect(lambda: close_dialog())
    # Return the same date that was given if cancelled.
    cancel_button.clicked.connect(lambda: close_dialog(initial_date))
    
    return dialog
