from flask import Blueprint, jsonify, request

api = Blueprint("api", __name__)

TASKS = []


@api.route("/")
def index():
    return jsonify({"message": "Flask CI/CD Demo API", "status": "running"})


@api.route("/health")
def health():
    return jsonify({"status": "healthy"})


@api.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify({"tasks": TASKS, "count": len(TASKS)})


@api.route("/tasks", methods=["POST"])
def create_task():
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
def update_task(task_id):
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
def delete_task(task_id):
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if task is None:
        return jsonify({"error": "task not found"}), 404

    TASKS.remove(task)
    return jsonify({"message": "task deleted"}), 200
