import pytest

from app.models.task import Task
from app.models.user import User
from app.modules.auth.security import create_access_token


@pytest.fixture
def task_access(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    return [
        {"Authorization": f"Bearer {create_access_token(user.id)}"} for user in users
    ]


@pytest.fixture
def saved_task(client, task_access):
    response = client.post(
        "/tasks",
        headers=task_access[0],
        json={
            "title": "Original",
            "description": "Details",
            "deadline": "Tomorrow",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_get_and_list_schema_and_persistence(client, task_access, db_session):
    response = client.post(
        "/tasks", headers=task_access[0], json={"title": " Work ", "priority": "HIGH"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data == {
        "id": data["id"],
        "title": "Work",
        "priority": "high",
        "description": None,
        "deadline": None,
        "completed": False,
        "created_at": data["created_at"],
    }
    assert data["created_at"]
    db_session.expire_all()
    assert db_session.get(Task, data["id"]).title == "Work"
    fetched = client.get(f"/tasks/{data['id']}", headers=task_access[0])
    assert fetched.status_code == 200
    assert fetched.json() == data
    assert client.get("/tasks", headers=task_access[0]).json() == [data]
    assert client.get("/tasks", headers=task_access[1]).json() == []


def test_patch_completion_and_delete_persist(
    client, task_access, saved_task, db_session
):
    path = f"/tasks/{saved_task}"
    response = client.patch(path, headers=task_access[0], json={"title": "Changed"})
    assert response.status_code == 200
    assert (
        response.json()["title"],
        response.json()["description"],
        response.json()["deadline"],
    ) == (
        "Changed",
        "Details",
        "Tomorrow",
    )
    response = client.patch(
        path, headers=task_access[0], json={"description": None, "deadline": None}
    )
    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["deadline"] is None
    for _ in range(2):
        response = client.patch(f"{path}/complete", headers=task_access[0])
        assert response.status_code == 200
        assert response.json()["completed"] is True
    db_session.expire_all()
    assert db_session.get(Task, saved_task).completed is True
    response = client.delete(path, headers=task_access[0])
    assert response.status_code == 204
    assert response.content == b""
    assert db_session.get(Task, saved_task) is None


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/tasks"),
        ("post", "/tasks"),
        ("get", "/tasks/1"),
        ("patch", "/tasks/1"),
        ("patch", "/tasks/1/complete"),
        ("delete", "/tasks/1"),
    ],
)
def test_authentication_required(client, method, path):
    assert client.request(method, path, json={"title": "Work"}).status_code == 401


@pytest.mark.parametrize(
    "method,suffix",
    [("get", ""), ("patch", ""), ("patch", "/complete"), ("delete", "")],
)
def test_other_users_cannot_access_task(
    client, task_access, saved_task, db_session, method, suffix
):
    response = client.request(
        method,
        f"/tasks/{saved_task}{suffix}",
        headers=task_access[1],
        json={"title": "Stolen"},
    )
    assert response.status_code == 401
    assert response.json()["success"] is False
    db_session.expire_all()
    task = db_session.get(Task, saved_task)
    assert (task.title, task.completed) == ("Original", False)


@pytest.mark.parametrize(
    "method,suffix",
    [("get", ""), ("patch", ""), ("patch", "/complete"), ("delete", "")],
)
def test_missing_task_returns_404(client, task_access, method, suffix):
    response = client.request(
        method, f"/tasks/999{suffix}", headers=task_access[0], json={"title": "Work"}
    )
    assert response.status_code == 404
    assert response.json()["success"] is False


@pytest.mark.parametrize(
    "body,status",
    [
        ({"title": "Changed", "priority": "urgent"}, 400),
        ({"title": " "}, 400),
        ({"deadline": "x" * 101}, 400),
        ({"description": 12}, 422),
    ],
)
def test_invalid_patch_does_not_change_task(
    client, task_access, saved_task, db_session, body, status
):
    response = client.patch(f"/tasks/{saved_task}", headers=task_access[0], json=body)
    assert response.status_code == status
    db_session.expire_all()
    assert db_session.get(Task, saved_task).title == "Original"


@pytest.mark.parametrize(
    "body,status",
    [({"title": " "}, 400), ({}, 422), ({"title": "Work", "deadline": 12}, 422)],
)
def test_invalid_creation_does_not_persist(
    client, task_access, db_session, body, status
):
    response = client.post("/tasks", headers=task_access[0], json=body)
    assert response.status_code == status
    assert db_session.query(Task).count() == 0
