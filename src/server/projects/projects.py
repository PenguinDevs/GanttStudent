"""
projects.py
Routes for creating, renaming, and deleting projects.
@jasonyi
Created 30/05/2024
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


class ProjectsRoute(WebAppRoutes):
    """Route for registering a new user."""

    routes = web.RouteTableDef()

    @routes.put("/project/new-project")
    async def new_project(request: web.Request) -> web.Response:
        """
        Create a new project using a given name.

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
        body = await parse_json_request(request, ["project_name"])
        if isinstance(body, web.Response):
            return body

        project_name = body["project_name"]
        # Validation checks.
        if project_name == "":
            return server.json_payload_response(400, {"message": "Project name cannot be empty."})
        elif len(project_name) > 50:
            return server.json_payload_response(400, {"message": "Project name must be 50 characters or less."})

        # Create the project.
        while True:
            uuid = str(uuid4())
            project_data = await server.db.read("projects", "project_data", {"_id": uuid})
            if project_data is None:
                break

        project_data = {
            "_id": uuid,
            "name": project_name,
            "admin": body["username"],
            "created_at": datetime.now(timezone.utc).timestamp(),
            "updated_at": datetime.now(timezone.utc).timestamp(),
            "invitees": [],
        }

        await server.db.update("projects", "project_data", {"_id": uuid}, project_data)

        return server.json_payload_response(200, {
            "message": "Project created.",
            "project_data": project_data,
            "access_token": body["access_token"]
        })
        
    @routes.post("/project/rename-project")
    async def rename_project(request: web.Request) -> web.Response:
        """
        Renames a new project using a uuid to a given name.

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
        body = await parse_json_request(request, ["uuid", "name"])
        if isinstance(body, web.Response):
            return body

        uuid = body["uuid"]
        name = body["name"]
        # Validation checks.
        if uuid == "":
            return server.json_payload_response(400, {"message": "uuid cannot be empty."})
        elif name == "":
            return server.json_payload_response(400, {"message": "Project name cannot be empty."})
        elif len(name) > 50:
            return server.json_payload_response(400, {"message": "Project name must be 50 characters or less."})

        # Find the project.
        project_data = await server.db.read("projects", "project_data", {"_id": uuid, "admin": body["username"]})
        if project_data is None:
            return server.json_payload_response(404, {"message": "Project not found or you do not have permissions to do this."})

        project_data["name"] = name
        project_data["updated_at"] = datetime.now(timezone.utc).timestamp()

        await server.db.update("projects", "project_data", {"_id": uuid}, project_data)

        return server.json_payload_response(200, {
            "message": "Project renamed.",
            "project_data": project_data,
            "access_token": body["access_token"]
        })
    
    @routes.post("/project/delete-project")
    async def delete_project(request: web.Request) -> web.Response:
        """
        Delete a project using a given uuid.

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
        body = await parse_json_request(request, ["uuid"])
        if isinstance(body, web.Response):
            return body

        uuid = body["uuid"]
        # Validation checks.
        if uuid == "":
            return server.json_payload_response(400, {"message": "uuid cannot be empty."})

        # Find the project.
        project_data = await server.db.read("projects", "project_data", {"_id": uuid, "admin": body["username"]})
        if project_data is None:
            return server.json_payload_response(404, {"message": "Project not found or you do not have permissions to do this."})
        
        # Delete the project.
        await server.db.erase("projects", "project_data", {"_id": uuid})
        # Delete its tasks.
        await server.db.erase_many("projects", "tasks", {"project_uuid": uuid})

        return server.json_payload_response(200, {
            "message": "Project deleted.",
            "uuid": uuid,
            "access_token": body["access_token"]
        })
    
    @routes.post("/project/fetch-user-projects")
    async def get_user_projects(request: web.Request) -> web.Response:
        """
        Fetch all projects that the user has access to.

        Args:
            request (web.Request): The request object.
        
        Returns:
            web.Response: The response object.
                400: Invalid JSON payload or invalid username/password.
                410: Access token expired.
                403: Invalid access token.
                200: Success.
        """
        server: WebServer = request.app.app
        body = await parse_json_request(request, [])
        if isinstance(body, web.Response):
            return body

        projects = {}
        async for project in await server.db.read_multi("projects", "project_data", {"admin": body["username"]}):
            projects[project["_id"]] = project

        return server.json_payload_response(200, {
            "message": "Project fetched.",
            "projects": projects,
            "access_token": body["access_token"]
        })
