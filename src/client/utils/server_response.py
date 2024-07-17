import json

from PyQt6.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt6.QtCore import QByteArray


def get_json_from_reply(reply: QNetworkReply) -> dict:
    response_bytes = reply.readAll()
    response_str = str(response_bytes, "utf-8")  # Convert QByteArray to string
    return json.loads(response_str)

def to_json_data(payload: dict) -> QByteArray:
    data = QByteArray()
    data.append(json.dumps(payload).encode("utf-8"))
    
    return data
