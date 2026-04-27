import json


def test_index(client):
    response = client.get("/")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["status"] == "running"


def test_health(client):
    response = client.get("/health")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["status"] == "healthy"


def test_get_tasks_empty(client):
    response = client.get("/tasks")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["count"] == 0


def test_create_task(client):
    response = client.post(
        "/tasks",
        data=json.dumps({"title": "Test task"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert response.status_code == 201
    assert data["title"] == "Test task"
    assert data["done"] is False


def test_create_task_missing_title(client):
    response = client.post(
        "/tasks",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_update_task(client):
    client.post(
        "/tasks",
        data=json.dumps({"title": "Task to update"}),
        content_type="application/json",
    )
    response = client.put(
        "/tasks/1",
        data=json.dumps({"done": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["done"] is True


def test_update_task_not_found(client):
    response = client.put(
        "/tasks/999",
        data=json.dumps({"done": True}),
        content_type="application/json",
    )
    assert response.status_code == 404


def test_delete_task(client):
    client.post(
        "/tasks",
        data=json.dumps({"title": "Task to delete"}),
        content_type="application/json",
    )
    response = client.delete("/tasks/1")
    assert response.status_code == 200


def test_delete_task_not_found(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
