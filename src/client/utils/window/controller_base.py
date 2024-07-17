from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6 import QtCore

if TYPE_CHECKING:
    from client.utils.window.page_base import BasePage
    from app import ClientApplication


class BaseController():
    """
    The base class for any controller, responsible for the behaviour of a
    window.
    """

    def __init__(self, client: ClientApplication, view: BasePage) -> None:
        """Class initialisation."""
        self._view = view
        self._client = client
        self._network_manager = client.network_manager
        self._setup_endpoints()
        self._connect_signals()

    def _setup_endpoints(self) -> None:
        """
        Sets up any QNetworkRequest objects used in this controller for
        communicating with servers.

        Returns:
            None
        """
        raise NotImplementedError()
    
    def _connect_signals(self) -> None:
        """
        Connects all input signals to its corresponding functions in this controller.

        Returns:
            None
        """
        raise NotImplementedError()

    def show(self) -> None:
        """
        Show the window associated with this controller.

        Returns:
            None
        """
        self._view.show()

    def hide(self) -> None:
        """
        Hide the window associated with this controller.

        Returns:
            None
        """
        self._view.hide()
