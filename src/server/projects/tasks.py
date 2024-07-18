"""Routes for creating, renaming, and deleting projects."""

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from uuid import uuid4
import math

from aiohttp import web

from base_router import WebAppRoutes

from utils.web import parse_json_request
if TYPE_CHECKING:
    from app import WebServer


class TasksRoute(WebAppRoutes):
    """Route for registering a new user."""

    routes = web.RouteTableDef()

    @routes.put("/project/edit/task/new-task")
    async def new_project(request: web.Request) -> web.Response:
        """
        Create a new task using a given name for a given project.

        Args:
            request (web.Request): The request object.
        
        Returns:
            web.Response: The response object.
                400: Invalid JSON payload.
                410: Access token expired.
                403: Invalid access token.
                200: Success.
        """
        server: WebServer = request.app.app
        body = await parse_json_request(request, ["project_uuid", "task_data"])
        if isinstance(body, web.Response):
            return body
        
        required_task_data_fields = {
            "task_type": (str, 4, 9),
            "name": (str, 1, 20),
            "description": (str, 0, 1024),
            "start_date": (int,),
            "end_date": (int,),
            "completed": (bool,),
            "colour": (str, 7, 7),
            "dependencies": (list,),
        }
        for field, validation_info in required_task_data_fields.items():
            if field in body["task_data"].keys():
                value = body["task_data"][field]
                try:
                    value = validation_info[0](value)
                    body["task_data"][field] = value
                except ValueError:
                    return server.json_payload_response(400, {"message": f"Field {field} type in task_data must be {validation_info[0]}, instead got: {type(field)}."})
                
                if validation_info[0] is str:
                    if len(value) < validation_info[1]:
                        return server.json_payload_response(400, {"message": f"{field} must be longer than {validation_info[1]} chars."})
                    elif len(value) > validation_info[2]:
                        return server.json_payload_response(400, {"message": f"{field} must be shorter than {validation_info[1]} chars."})
            else:
                return server.json_payload_response(400, {"message": f"Missing field in task_data: {field}."})

        if not body["task_data"]["task_type"] in ("task", "milestone"):
            return server.json_payload_response(400, {"message": f"task_type must be one of task or milestone."})

        project_uuid = body["project_uuid"]
        # Validation checks.
        if project_uuid == "":
            return server.json_payload_response(400, {"message": "Project uuid cannot be empty."})

        project_data = await server.db.read("projects", "project_data", {"_id": project_uuid})
        if project_data["admin"] != body["username"]:
            return server.json_payload_response(403, {"message": "You don't have access to this project."})

        while True:
            uuid = str(uuid4())
            task_data = await server.db.read("projects", "tasks", {"task_uuid": uuid, "project_uuid": project_uuid})
            if task_data is None:
                break
        
        task_data = body["task_data"]
        task_data["task_uuid"] = uuid
        task_data["project_uuid"] = project_uuid
        task_data["_id"] = f"{uuid}_{project_uuid}"

        project_data["tasks"].append(uuid)

        await server.db.update("projects", "tasks", {"_id": task_data["_id"]}, task_data)
        await server.db.update("projects", "project_data", {"_id": project_data["_id"]}, project_data)

        return server.json_payload_response(200, {
            "message": "Task created.",
            "task_data": task_data,
            "access_token": body["access_token"],
        })
