# signals_slots.py

"""Signals and slots example."""

import sys
from functools import partial

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

def greet(name):
    if msg.text():
        msg.setText("")
    else:
        msg.setText(f"Hello, {name}")

app = QApplication([])
window = QWidget()
window.setWindowTitle("Signals and slots")
layout = QVBoxLayout()

button = QPushButton("Greet")
button.clicked.connect(partial(greet, "World!"))

layout.addWidget(button)
msg = QLabel("")
layout.addWidget(msg)
window.setLayout(layout)
window.show()
sys.exit(app.exec())