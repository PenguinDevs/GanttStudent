"""Server application for the backend API."""

import os
from dotenv import load_dotenv
from aiohttp import web

from db import MongoDB

from authentication.register import RegisterRoute
from authentication.login import LoginRoute
from projects.projects import ProjectsRoute

load_dotenv()


class WebServer():
    def __init__(self, app: web.Application, routes: list, db: MongoDB):
        # NOTE: Cyclic reference here. Will cause memory leaks if intended to delete.
        self.app = app
        self.app.app = self
        
        self.db = db

        self._route_classes = routes
        self._routes = {}
        self._initialise_routes()

    def json_payload_response(self, status: int, data: dict) -> web.Response:
        data['status'] = status
        return web.json_response(data, status=status)
    
    def _initialise_routes(self):
        for route in self._route_classes:
            self._routes[route] = route(self)

    def run(self):
        """
        Run the server indefinitely, until forcefully stopped.
        """
        web.run_app(self.app)

if __name__ == "__main__":
    db = MongoDB(address=os.getenv('MONGO_ADDRESS'), username=os.getenv('MONGO_USER'), password=os.getenv('MONGO_PASS'))
    app = web.Application()
    server = WebServer(app, [
        RegisterRoute,
        LoginRoute,
        ProjectsRoute,
    ], db)

    # This runs indefinitely until the server is forcefully stopped.
    server.run()
