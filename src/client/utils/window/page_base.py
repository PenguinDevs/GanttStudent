"""
page_base.py
Page base class for the window system.
@jasonyi
Created 16/05/2024
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget
from PyQt6 import uic

if TYPE_CHECKING:
    from utils.window.controller_base import BaseController

class BasePage(QWidget):
    """The base class for any page."""
    
    # The path to the .ui file for the page.
    ui_path = ''

    def __init__(self) -> None:
        """Class initialisation."""
        super().__init__()
        self._load_ui()

    def _load_ui(self) -> QWidget:
        """
        Load the .ui file for the page, specified by self.ui_path.

        Returns:
            QWidget: A QWidget object.
        """
        return uic.load_ui.loadUi(self.ui_path, self)
    
    def assign_controller(self, controller: BaseController) -> None:
        """
        Assign the controller object associated or responsible for the behaviour
        of this page.
        """
        self._controller = controller
