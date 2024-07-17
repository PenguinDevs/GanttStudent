"""This module contains web utility functions for the web server."""

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime, timedelta, timezone

from aiohttp import web

from utils.crypto import is_access_token_valid, decode_jwt, get_access_token
if TYPE_CHECKING:
    from app import WebServer

RENEW_AHEAD_AT = 60*10 # 10 minutes


async def parse_json_request(request: web.Response, required_fields: list, requires_auth: bool = True) -> web.Response | dict:
    server: WebServer = request.app.app

    try:
        body = await request.json()
    except:
        return server.json_payload_response(400, {"message": "Invalid JSON payload."})
    
    if requires_auth is True:
        required_fields.append("access_token")
    
    if any([body.get(field) is None for field in required_fields]):
        return server.json_payload_response(400, {"message": "Missing field(s)."})
    
    if requires_auth is True:
        access_token = body["access_token"]
        decoded = decode_jwt(access_token)
        username = decoded["sub"]
        expires_at = decoded["exp"]

        body["username"] = username

        user = await server.db.read("users", "accounts", {"username": username})

        is_valid, message = is_access_token_valid(user["secret_key"], access_token)
        if is_valid is False:
            if message == 'expired':
                return server.json_payload_response(410, {"message": "Access expired."})
            else:
                return server.json_payload_response(403, {"message": "Invalid access token."})
        
        # Renew the access token if it is about to expire.
        if datetime.fromtimestamp(expires_at, timezone.utc) < datetime.now(timezone.utc) + timedelta(seconds=RENEW_AHEAD_AT):
            access_token = get_access_token(username, user["secret_key"])
            body["access_token"] = access_token
    
    # Success!
    return body