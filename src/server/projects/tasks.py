"""
routes.py
Routes for creating, renaming, and deleting tasks.
@jasonyi
Created 12/06/2024
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from uuid import uuid4

from aiohttp import web

from base_router import WebAppRoutes

from utils.web import parse_json_request
if TYPE_CHECKING:
    from app import WebServer


class TasksRoute(WebAppRoutes):
    """Route for registering a new user."""

    routes = web.RouteTableDef()

    @routes.put("/project/task/new")
    async def new_task(request: web.Request) -> web.Response:
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
        
        # Validation checks.
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

        # Validate that all the required fields are present.
        for field, validation_info in required_task_data_fields.items():
            if field in body["task_data"].keys():
                value = body["task_data"][field]

                # Type check.
                try:
                    value = validation_info[0](value)
                    body["task_data"][field] = value
                except ValueError:
                    return server.json_payload_response(400, {"message": f"Field {field} type in task_data must be {validation_info[0]}, instead got: {type(field)}."})
                
                if validation_info[0] is str:
                    # Range check (string length).
                    if len(value) < validation_info[1]:
                        return server.json_payload_response(400, {"message": f"{field} must be longer than or equal to {validation_info[1]} characters."})
                    elif len(value) > validation_info[2]:
                        return server.json_payload_response(400, {"message": f"{field} must be shorter than or equal to {validation_info[2]} characters."})
            else:
                return server.json_payload_response(400, {"message": f"Missing field in task_data: {field}."})
        
        # Validate that there are no extra fields in the task_data.
        for field in body["task_data"].keys():
            if field not in required_task_data_fields.keys():
                return server.json_payload_response(400, {"message": f"Invalid field in task_data: {field}."})

        # Validate that the task_type is valid.
        if not body["task_data"]["task_type"] in ("task", "milestone"):
            return server.json_payload_response(400, {"message": f"task_type must be one of task or milestone."})

        project_uuid = body["project_uuid"]
        # Existence check.
        if project_uuid == "":
            return server.json_payload_response(400, {"message": "Project uuid cannot be empty."})

        project_data = await server.db.read("projects", "project_data", {"_id": project_uuid})
        # Check if the user has access to the project.
        if project_data["admin"] != body["username"] and body["username"] not in project_data["invitees"]:
            return server.json_payload_response(403, {"message": "You don't have access to this project."})

        # Obtain a unique task uuid that does not already exist in the database for the project.
        while True:
            uuid = str(uuid4())
            task_data = await server.db.read("projects", "tasks", {"task_uuid": uuid, "project_uuid": project_uuid})
            if task_data is None:
                break
        
        # Get the total number of tasks in the project.
        total_tasks = await server.db.count("projects", "tasks", {"project_uuid": body["project_uuid"]})

        task_data = body["task_data"]
        task_data["row"] = total_tasks
        task_data["task_uuid"] = uuid
        task_data["project_uuid"] = project_uuid
        task_data["_id"] = f"{uuid}:{project_uuid}"

        # Save.
        await server.db.update("projects", "tasks", {"_id": task_data["_id"]}, task_data)
        await server.db.update("projects", "project_data", {"_id": project_uuid}, {"updated_at": datetime.now(timezone.utc).timestamp()})

        return server.json_payload_response(200, {
            "message": "Task created.",
            "task_data": task_data,
            "access_token": body["access_token"],
        })
    
    
    @routes.post("/project/task/update")
    async def update_task(request: web.Request) -> web.Response:
        """
        Update a task using the given information for a given project.

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
        
        # Validation checks.
        required_task_data_fields = {
            "_id": (str, 36*2+1, 36*2+1),
            "task_uuid": (str, 36, 36),
            "project_uuid": (str, 36, 36),
            "task_type": (str, 4, 9),
            "row": (int,),
            "name": (str, 1, 20),
            "description": (str, 0, 1024),
            "start_date": (int,),
            "end_date": (int,),
            "completed": (bool,),
            "colour": (str, 7, 7),
            "dependencies": (list,),
        }

        # Validate that all the required fields are present.
        for field, validation_info in required_task_data_fields.items():
            if field in body["task_data"].keys():
                value = body["task_data"][field]
                
                # Type check.
                try:
                    value = validation_info[0](value)
                    body["task_data"][field] = value
                except ValueError:
                    return server.json_payload_response(400, {"message": f"Field {field} type in task_data must be {validation_info[0]}, instead got: {type(field)}."})
                
                if validation_info[0] is str:
                    # Range check (string length).
                    if len(value) < validation_info[1]:
                        return server.json_payload_response(400, {"message": f"{field} must be longer than {validation_info[1]} chars."})
                    elif len(value) > validation_info[2]:
                        return server.json_payload_response(400, {"message": f"{field} must be shorter than {validation_info[1]} chars."})
            else:
                return server.json_payload_response(400, {"message": f"Missing field in task_data: {field}."})

        # Validate that there are no extra fields in the task_data.
        for field in body["task_data"].keys():
            if field not in required_task_data_fields.keys():
                return server.json_payload_response(400, {"message": f"Invalid field in task_data: {field}."})

        # Validate that the task_type is valid.
        if not body["task_data"]["task_type"] in ("task", "milestone"):
            return server.json_payload_response(400, {"message": f"task_type must be one of task or milestone."})

        project_uuid = body["project_uuid"]
        # Existence check.
        if project_uuid == "":
            return server.json_payload_response(400, {"message": "Project uuid cannot be empty."})

        project_data = await server.db.read("projects", "project_data", {"_id": project_uuid})
        # Check if the user has access to the project.
        if project_data["admin"] != body["username"] and body["username"] not in project_data["invitees"]:
            return server.json_payload_response(403, {"message": "You don't have access to this project."})
        
        # Save.
        await server.db.update("projects", "tasks", {"_id": body["task_data"]["_id"]}, body["task_data"])
        await server.db.update("projects", "project_data", {"_id": project_uuid}, {"updated_at": datetime.now(timezone.utc).timestamp()})

        return server.json_payload_response(200, {
            "message": "Task updated.",
            "task_data": body["task_data"],
            "access_token": body["access_token"],
        })
    
    @routes.post("/project/task/delete")
    async def delete_task(request: web.Request) -> web.Response:
        """
        Delete a new task using a given uuid for a given project.

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
        body = await parse_json_request(request, ["project_uuid", "task_uuid"])
        if isinstance(body, web.Response):
            return body

        project_uuid = body["project_uuid"]
        task_uuid = body["task_uuid"]
        # Existence check.
        if project_uuid == "":
            return server.json_payload_response(400, {"message": "Project uuid cannot be empty."})

        project_data = await server.db.read("projects", "project_data", {"_id": project_uuid})
        # Check if the user has access to the project.
        if project_data["admin"] != body["username"] and body["username"] not in project_data["invitees"]:
            return server.json_payload_response(403, {"message": "You don't have access to this project."})
        
        task_data = await server.db.read("projects", "tasks", {"task_uuid": task_uuid, "project_uuid": project_uuid})
        if task_data is None:
            return server.json_payload_response(404, {"message": "Task not found."})

        # Delete.
        await server.db.erase("projects", "tasks", {"task_uuid": task_uuid})
        
        if await server.db.count("projects", "tasks", {"project_uuid": project_uuid, "row": {"$gt": task_data["row"]}}) > 0:
            # Shift all tasks with a row greater than the deleted task's row down by 1.
            await server.db.update_many("projects", "tasks", {"project_uuid": project_uuid, "row": {"$gt": task_data["row"]}}, inc={"row": -1})
        
        await server.db.update_many("projects", "tasks", {"project_uuid": project_uuid}, pull={"dependencies": task_uuid})
        await server.db.update("projects", "project_data", {"_id": project_uuid}, {"updated_at": datetime.now(timezone.utc).timestamp()})
        
        return server.json_payload_response(200, {
            "message": "Task updated.",
            "task_uuid": task_uuid,
            "access_token": body["access_token"],
        })

    @routes.post("/project/task/fetch-all")
    async def fetch_tasks(request: web.Request) -> web.Response:
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
        body = await parse_json_request(request, ["project_uuid"])
        if isinstance(body, web.Response):
            return body

        project_uuid = body["project_uuid"]
        
        # Existence check.
        if project_uuid == "":
            return server.json_payload_response(400, {"message": "Project uuid cannot be empty."})

        project_data = await server.db.read("projects", "project_data", {"_id": project_uuid})
        # Check if the user has access to the project.
        if project_data["admin"] != body["username"] and body["username"] not in project_data["invitees"]:
            return server.json_payload_response(403, {"message": "You don't have access to this project."})

        # Collect all tasks for the project.
        tasks = {}
        async for task in await server.db.read_multi("projects", "tasks", {"project_uuid": project_uuid}):
            tasks[task["task_uuid"]] = task
            
        await server.db.update("projects", "project_data", {"_id": project_uuid}, {"updated_at": datetime.now(timezone.utc).timestamp()})

        return server.json_payload_response(200, {
            "message": "Tasks fetched.",
            "tasks": tasks,
            "access_token": body["access_token"],
        })
