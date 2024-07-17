from __future__ import annotations
from aiohttp import web

from base_router import WebAppRoutes
from typing import TYPE_CHECKING

from utils.crypto import hash_password, generate_secret_key, get_access_token
if TYPE_CHECKING:
    from app import WebServer

class RegisterRoute(WebAppRoutes):
    """Route for registering a new user."""

    routes = web.RouteTableDef()

    @routes.post("/user/register")
    async def register_user(request: web.Request) -> web.Response:
        """
        Register a new user.

        Args:
            request (web.Request): The request object.
        
        Returns:
            web.Response: The response object.
                400: Invalid JSON payload or invalid username/password.
                409: User already exists.
                200: Success.
        """
        server: WebServer = request.app.app

        try:
            body = await request.json()
        except:
            return server.json_payload_response(400, {"message": "Invalid JSON payload."})
        
        if body.get("username") is None or body.get("password") is None:
            return server.json_payload_response(400, {"message": "Missing username or password."})
        
        username: str = body["username"]
        password: str = body["password"]

        user = await server.db.read("users", "accounts", {"username": username})
        if not user is None:
            return server.json_payload_response(409, {"message": "User already exists."})
        
        if len(username) > 32:
            return server.json_payload_response(400, {"message": "Username too long. Must be at most 32 characters."})
        elif len(username) < 4:
            return server.json_payload_response(400, {"message": "Username too short. Must be at least 4 characters."})
        elif not any(char.isalnum() for char in username):
            return server.json_payload_response(400, {"message": "Username must contain only letters and numbers."})
        
        if len(password) < 8 or len(password) > 32:
            return server.json_payload_response(400, {"message": "Password must be between 8 and 32 characters."})
        elif password.lower() == password:
            return server.json_payload_response(400, {"message": "Password must contain at least one uppercase letter."})
        elif password.upper() == password:
            return server.json_payload_response(400, {"message": "Password must contain at least one lowercase letter."})
        elif not any(char.isdigit() for char in password):
            return server.json_payload_response(400, {"message": "Password must contain at least one number."})
        elif not any(char.isalpha() for char in password):
            return server.json_payload_response(400, {"message": "Password must contain at least one letter."})
        elif not any(not char.isalnum() for char in password):
            return server.json_payload_response(400, {"message": "Password must contain at least one special character."})
    
        secret = generate_secret_key()
        user = {
            "username": username,
            "password_hash": hash_password(username, password),
            "secret_key": secret
        }

        await server.db.write("users", "accounts", user)

        return server.json_payload_response(200, {
            "message": "User registered.",
            "username": username
        })
