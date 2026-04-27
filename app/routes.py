"""
Routes
======

REST API endpoints for task management.

All endpoints return JSON responses. Tasks are stored in memory
(no database) for simplicity.

Endpoints summary
-----------------

====== ================== ==========================
Method Endpoint           Description
====== ================== ==========================
GET    ``/``              API information
GET    ``/health``        Health check
GET    ``/tasks``         List all tasks
POST   ``/tasks``         Create a new task
PUT    ``/tasks/<id>``    Update an existing task
DELETE ``/tasks/<id>``    Delete a task
====== ================== ==========================
"""

from typing import Any

from flask import Blueprint, Response, jsonify, request

api = Blueprint("api", __name__)

TASKS: list[dict[str, Any]] = []
"""In-memory task storage. Each task is a dict with keys
``id`` (int), ``title`` (str), and ``done`` (bool)."""


@api.route("/")
def index() -> Response:
    """Return API information and current status.

    :returns: JSON with ``message`` and ``status`` fields.
    :status 200: Always.
    """
    return jsonify({"message": "Flask CI/CD Demo API", "status": "running"})


@api.route("/health")
def health() -> Response:
    """Health check endpoint.

    Used by deployment pipelines to verify the application is
    running correctly after a deploy.

    :returns: JSON ``{"status": "healthy"}``.
    :status 200: Application is healthy.
    """
    return jsonify({"status": "healthy"})


@api.route("/tasks", methods=["GET"])
def get_tasks() -> Response:
    """List all tasks.

    :returns: JSON with ``tasks`` (list) and ``count`` (int).
    :status 200: Always.
    """
    return jsonify({"tasks": TASKS, "count": len(TASKS)})


@api.route("/tasks", methods=["POST"])
def create_task() -> tuple[Response, int]:
    """Create a new task.

    Expects a JSON body with a ``title`` field.

    :returns: The created task object.
    :status 201: Task created successfully.
    :status 400: ``title`` field is missing from request body.

    Example request body::

        {"title": "Buy groceries"}
    """
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title is required"}), 400

    task = {
        "id": len(TASKS) + 1,
        "title": data["title"],
        "done": False,
    }
    TASKS.append(task)
    return jsonify(task), 201


@api.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id: int) -> tuple[Response, int] | Response:
    """Update an existing task.

    Accepts optional ``title`` (str) and ``done`` (bool) fields
    in the JSON body. Only provided fields are updated.

    :param task_id: The ID of the task to update.
    :returns: The updated task object.
    :status 200: Task updated successfully.
    :status 404: No task found with the given ID.
    """
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if task is None:
        return jsonify({"error": "task not found"}), 404

    data = request.get_json()
    if data.get("title"):
        task["title"] = data["title"]
    if "done" in data:
        task["done"] = data["done"]

    return jsonify(task)


@api.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id: int) -> tuple[Response, int]:
    """Delete a task.

    :param task_id: The ID of the task to delete.
    :returns: Confirmation message.
    :status 200: Task deleted successfully.
    :status 404: No task found with the given ID.
    """
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if task is None:
        return jsonify({"error": "task not found"}), 404

    TASKS.remove(task)
    return jsonify({"message": "task deleted"}), 200
