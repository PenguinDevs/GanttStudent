from __future__ import annotations
from aiohttp import web

from base_router import WebAppRoutes
from typing import TYPE_CHECKING

from utils.web import parse_json_request
from utils.crypto import hash_password, get_access_token
if TYPE_CHECKING:
    # Importing only for type checking purposes. This is not imported when the
    # code is run.
    from app import WebServer

class LoginRoute(WebAppRoutes):
    """Route for logging in as a user."""

    routes = web.RouteTableDef()

    @routes.post("/user/authorise")
    async def login_user(request: web.Request) -> web.Response:
        """
        Register a new user.

        Args:
            request (web.Request): The request object.
        
        Returns:
            web.Response: The response object.
                400: Invalid JSON payload.
                401: Username or password is incorrect.
                200: Success.
        """
        server: WebServer = request.app.app
        body = await parse_json_request(request, ["username", "password"], requires_auth=False)
        if isinstance(body, web.Response):
            return body

        try:
            body = await request.json()
        except:
            return server.json_payload_response(400, {"message": "Invalid JSON payload."})
        
        if body.get("username") is None or body.get("password") is None:
            return server.json_payload_response(401, {"message": "Username or password is incorrect."})
        
        username: str = body["username"]
        password: str = body["password"]

        user = await server.db.read("users", "accounts", {"username": username})
        if user is None:
            return server.json_payload_response(404, {"message": "This user does not exist."})
        
        if hash_password(username, password) != user["password_hash"]:
            return server.json_payload_response(401, {"message": "Username or password is incorrect."})

        return server.json_payload_response(200, {
            "message": "Success.",
            "access_token": get_access_token(username, user["secret_key"])
        })
