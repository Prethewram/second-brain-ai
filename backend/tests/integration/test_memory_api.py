import pytest

from app.models.memory import Memory
from app.models.user import User
from app.modules.auth.security import create_access_token


@pytest.fixture
def memory_access(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    memory = Memory(
        user_id=users[0].id, content="Original", category="general", importance=1
    )
    db_session.add(memory)
    db_session.commit()
    headers = [
        {"Authorization": f"Bearer {create_access_token(user.id)}"} for user in users
    ]
    return memory.id, headers


def test_list_returns_owned_memory_schema(client, memory_access):
    memory_id, headers = memory_access
    response = client.get("/memory", headers=headers[0])
    assert response.status_code == 200
    assert response.json()[0] == {
        "id": memory_id,
        "content": "Original",
        "category": "general",
        "importance": 1,
        "created_at": response.json()[0]["created_at"],
    }
    assert response.json()[0]["created_at"]
    assert client.get("/memory", headers=headers[1]).json() == []


def test_update_and_delete_persist(client, memory_access, db_session):
    memory_id, headers = memory_access
    response = client.put(
        f"/memory/{memory_id}",
        headers=headers[0],
        json={
            "content": "Updated",
            "category": "work",
            "importance": 5,
        },
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated"
    db_session.expire_all()
    assert db_session.get(Memory, memory_id).importance == 5
    response = client.delete(f"/memory/{memory_id}", headers=headers[0])
    assert response.status_code == 200
    assert response.json() == {"message": "Memory deleted"}
    assert db_session.get(Memory, memory_id) is None


@pytest.mark.parametrize(
    "method,path", [("get", "/memory"), ("put", "/memory/1"), ("delete", "/memory/1")]
)
def test_authentication_required(client, method, path):
    response = client.request(
        method, path, json={"content": "New", "category": "general", "importance": 1}
    )
    assert response.status_code == 401


@pytest.mark.parametrize("method", ["put", "delete"])
def test_other_users_cannot_modify_memory(client, memory_access, db_session, method):
    memory_id, headers = memory_access
    response = client.request(
        method,
        f"/memory/{memory_id}",
        headers=headers[1],
        json={
            "content": "Stolen",
            "category": "general",
            "importance": 1,
        },
    )
    assert (
        response.status_code == 401
    )  # Existing application's ownership error contract.
    assert response.json()["success"] is False
    db_session.expire_all()
    assert db_session.get(Memory, memory_id).content == "Original"


@pytest.mark.parametrize("method", ["put", "delete"])
def test_missing_memory_returns_404(client, memory_access, method):
    _, headers = memory_access
    response = client.request(
        method,
        "/memory/999",
        headers=headers[0],
        json={
            "content": "New",
            "category": "general",
            "importance": 1,
        },
    )
    assert response.status_code == 404
    assert response.json()["success"] is False


@pytest.mark.parametrize(
    "body,status",
    [
        ({"content": " ", "category": "general", "importance": 1}, 400),
        ({"content": "New", "category": "general", "importance": "invalid"}, 422),
    ],
)
def test_invalid_updates_return_validation_errors(
    client, memory_access, db_session, body, status
):
    memory_id, headers = memory_access
    response = client.put(f"/memory/{memory_id}", headers=headers[0], json=body)
    assert response.status_code == status
    db_session.expire_all()
    assert db_session.get(Memory, memory_id).content == "Original"
