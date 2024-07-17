from __future__ import annotations
from typing import TYPE_CHECKING
import json

from PyQt6.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt6.QtCore import QByteArray

if TYPE_CHECKING:
    from app import ClientApplication

def get_json_from_reply(reply: QNetworkReply) -> dict:
    response_bytes = reply.readAll()
    response_str = str(response_bytes, "utf-8")  # Convert QByteArray to string
    return json.loads(response_str)

def to_json_data(payload: dict) -> QByteArray:
    data = QByteArray()
    data.append(json.dumps(payload).encode("utf-8"))
    
    return data

def handle_new_response_payload(client: ClientApplication, payload: dict) -> None:
    if "access_token" in payload.keys():
        if payload.get("access_token") is None:
            return
        client.cache["access_token"] = payload["access_token"]
        client.save_cache()
