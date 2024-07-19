"""Functions for handling server responses."""

from __future__ import annotations
from typing import TYPE_CHECKING
import json

from PyQt6.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt6.QtCore import QByteArray

if TYPE_CHECKING:
    from app import ClientApplication

def get_json_from_reply(reply: QNetworkReply) -> dict | None:
    """
    Get the JSON data from a network reply object.
    
    Args:
        reply: The network reply object.
    
    Returns:
        dict | None: The JSON data from the reply, or None if the data could not
            be decoded.
    """
    response_bytes = reply.readAll()
    response_str = str(response_bytes, "utf-8")  # Convert QByteArray to string
    try:
        return json.loads(response_str)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return None

def to_json_data(payload: dict) -> QByteArray | None:
    """
    Convert a dictionary to a QByteArray object.

    Args:
        payload (dict): The dictionary to convert.

    Returns:
        QByteArray | None: The QByteArray object, or None if the data could not
            be encoded.
    """
    data = QByteArray()
    try:
        data.append(json.dumps(payload).encode("utf-8"))
        return data
    except json.JSONDecodeError as e:
        print(f"Failed to encode JSON: {e}")
        return None

def handle_new_response_payload(client: ClientApplication, payload: dict) -> None:
    """
    Handle a new response payload from the server.

    This function will check the payload for an access token, and update it in
    the client cache if it is present.

    Args:
        client (ClientApplication): The client application object.
        payload (dict): The payload from the server.
    """
    if "access_token" in payload.keys():
        if payload.get("access_token") is None:
            return
        client.cache["access_token"] = payload["access_token"]
        client.save_cache()
