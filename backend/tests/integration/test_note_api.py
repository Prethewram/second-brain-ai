import pytest

from app.models.notes import Note
from app.models.user import User
from app.modules.auth.security import create_access_token


@pytest.fixture
def note_access(db_session):
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
def saved_note(client, note_access):
    response = client.post(
        "/notes", headers=note_access[0], json={"title": "Original", "content": "Text"}
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_get_return_schema_and_persist(client, note_access, db_session):
    response = client.post(
        "/notes",
        headers=note_access[0],
        json={
            "title": " Idea ",
            "content": " Details ",
            "category": " WORK ",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data == {
        "id": data["id"],
        "title": "Idea",
        "content": "Details",
        "category": "work",
        "source": "manual",
        "is_archived": False,
    }
    db_session.expire_all()
    assert db_session.get(Note, data["id"]).content == "Details"
    fetched = client.get(f"/notes/{data['id']}", headers=note_access[0])
    assert fetched.status_code == 200
    assert fetched.json() == data
    assert client.get("/notes", headers=note_access[1]).json() == []


def test_patch_archive_restore_and_delete(client, note_access, saved_note, db_session):
    path = f"/notes/{saved_note}"
    response = client.patch(path, headers=note_access[0], json={"title": "Changed"})
    assert response.status_code == 200
    assert response.json()["content"] == "Text"
    assert response.json()["title"] == "Changed"
    assert client.patch(f"{path}/archive", headers=note_access[0]).status_code == 200
    assert client.get("/notes", headers=note_access[0]).json() == []
    assert client.get(path, headers=note_access[0]).json()["is_archived"] is True
    response = client.patch(path, headers=note_access[0], json={"is_archived": False})
    assert response.status_code == 200
    assert response.json()["is_archived"] is False
    assert len(client.get("/notes", headers=note_access[0]).json()) == 1
    response = client.delete(path, headers=note_access[0])
    assert response.status_code == 204
    assert response.content == b""
    assert db_session.get(Note, saved_note) is None


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/notes"),
        ("post", "/notes"),
        ("get", "/notes/1"),
        ("patch", "/notes/1"),
        ("patch", "/notes/1/archive"),
        ("delete", "/notes/1"),
    ],
)
def test_authentication_required(client, method, path):
    response = client.request(method, path, json={"title": "Title", "content": "Text"})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "method,suffix", [("get", ""), ("patch", ""), ("patch", "/archive"), ("delete", "")]
)
def test_other_users_cannot_access_note(
    client, note_access, saved_note, db_session, method, suffix
):
    response = client.request(
        method,
        f"/notes/{saved_note}{suffix}",
        headers=note_access[1],
        json={"title": "Stolen"},
    )
    assert response.status_code == 401
    assert response.json()["success"] is False
    db_session.expire_all()
    note = db_session.get(Note, saved_note)
    assert (note.title, note.is_archived) == ("Original", False)


@pytest.mark.parametrize(
    "method,suffix", [("get", ""), ("patch", ""), ("patch", "/archive"), ("delete", "")]
)
def test_missing_note_returns_404(client, note_access, method, suffix):
    response = client.request(
        method, f"/notes/999{suffix}", headers=note_access[0], json={"title": "New"}
    )
    assert response.status_code == 404
    assert response.json()["success"] is False


@pytest.mark.parametrize(
    "body,status",
    [
        ({"title": "New", "content": " "}, 400),
        ({"title": "x" * 256}, 400),
        ({"content": 123}, 422),
    ],
)
def test_invalid_patch_preserves_note(
    client, note_access, saved_note, db_session, body, status
):
    response = client.patch(f"/notes/{saved_note}", headers=note_access[0], json=body)
    assert response.status_code == status
    db_session.expire_all()
    note = db_session.get(Note, saved_note)
    assert (note.title, note.content) == ("Original", "Text")
