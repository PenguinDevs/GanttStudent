"""Base class for routes to be added to the web server routing table."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import WebServer


class WebAppRoutes():
    """Base class for routes to be added to the web server routing table."""

    # The routes to be added to the web server.
    _routes_to_add = []

    def __init__(self, web_server: WebServer) -> None:
        """Class initialisation."""
        self.web_server = web_server

        self.web_server.app.add_routes(self.routes)
