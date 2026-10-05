import pytest

from app.models.meeting import Meeting
from app.models.notes import Note
from app.models.task import Task
from app.models.user import User
from app.modules.auth.security import create_access_token


@pytest.fixture
def meeting_access(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    return [
        {"Authorization": f"Bearer {create_access_token(user.id)}"} for user in users
    ]


def create_mom(client, headers):
    response = client.post(
        "/meetings",
        headers=headers,
        json={
            "title": "Planning",
            "meeting_date": "2026-10-05",
            "attendees": "Alex, Sam",
            "agenda": "Plan release",
            "minutes": "Discussed the release plan",
            "decisions": "Ship Friday",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_meeting_structure_and_children_share_the_library(
    client, meeting_access, db_session
):
    headers = meeting_access[0]
    meeting = create_mom(client, headers)
    note = client.post(
        f"/meetings/{meeting['id']}/notes",
        headers=headers,
        json={"title": "Release context", "content": "Agreed on scope"},
    )
    task = client.post(
        f"/meetings/{meeting['id']}/tasks",
        headers=headers,
        json={"title": "Prepare release", "priority": "high", "deadline": "Friday"},
    )
    assert note.status_code == task.status_code == 201
    assert db_session.query(Note).one().meeting_id == meeting["id"]
    assert db_session.query(Task).one().meeting_id == meeting["id"]
    detail = client.get(f"/meetings/{meeting['id']}", headers=headers).json()
    assert detail["notes"][0]["id"] == note.json()["id"]
    assert detail["tasks"][0]["id"] == task.json()["id"]
    assert client.get("/notes", headers=headers).json()[0]["id"] == note.json()["id"]
    assert client.get("/tasks", headers=headers).json()[0]["id"] == task.json()["id"]
    completed = client.patch(f"/tasks/{task.json()['id']}/complete", headers=headers)
    assert completed.status_code == 200
    assert (
        client.get(f"/meetings/{meeting['id']}", headers=headers).json()["tasks"][0][
            "completed"
        ]
        is True
    )
    update = client.put(
        f"/meetings/{meeting['id']}",
        headers=headers,
        json={
            "title": "Revised planning",
            "minutes": "Updated",
            "decisions": "Ship Monday",
        },
    )
    assert update.status_code == 200
    assert update.json()["meeting_date"] is None
    assert (
        client.get("/meetings", headers=headers).json()[0]["title"]
        == "Revised planning"
    )


def test_other_user_cannot_read_modify_delete_or_add_children(
    client, meeting_access, db_session
):
    meeting = create_mom(client, meeting_access[0])
    path = f"/meetings/{meeting['id']}"
    assert client.get("/meetings", headers=meeting_access[1]).json() == []
    for response in [
        client.get(path, headers=meeting_access[1]),
        client.put(
            path,
            headers=meeting_access[1],
            json={"title": "Stolen", "minutes": "Private"},
        ),
        client.delete(path, headers=meeting_access[1]),
        client.post(
            path + "/notes",
            headers=meeting_access[1],
            json={"title": "Intrusion", "content": "No"},
        ),
        client.post(
            path + "/tasks", headers=meeting_access[1], json={"title": "Intrusion"}
        ),
    ]:
        assert response.status_code == 404
    assert db_session.query(Meeting).one().title == "Planning"
    assert db_session.query(Note).count() == db_session.query(Task).count() == 0


def test_deleting_meeting_preserves_notes_and_tasks(client, meeting_access, db_session):
    headers = meeting_access[0]
    meeting = create_mom(client, headers)
    for suffix, body in [
        ("notes", {"title": "Keep note", "content": "Context"}),
        ("tasks", {"title": "Keep task"}),
    ]:
        assert (
            client.post(
                f"/meetings/{meeting['id']}/{suffix}", headers=headers, json=body
            ).status_code
            == 201
        )
    assert (
        client.delete(f"/meetings/{meeting['id']}", headers=headers).status_code == 204
    )
    db_session.expire_all()
    assert db_session.query(Meeting).count() == 0
    assert db_session.query(Note).one().meeting_id is None
    assert db_session.query(Task).one().meeting_id is None


@pytest.mark.parametrize(
    "body",
    [
        {"title": " ", "minutes": "Text"},
        {"title": "Meeting", "minutes": " "},
        {"title": "Meeting", "minutes": "Text", "meeting_date": "not-a-date"},
    ],
)
def test_invalid_mom_is_rejected_before_writes(
    client, meeting_access, db_session, body
):
    assert (
        client.post("/meetings", headers=meeting_access[0], json=body).status_code
        == 422
    )
    assert db_session.query(Meeting).count() == 0


def test_missing_meeting_and_authentication_are_required(client, meeting_access):
    assert client.get("/meetings").status_code == 401
    assert (
        client.post(
            "/meetings", json={"title": "Meeting", "minutes": "Text"}
        ).status_code
        == 401
    )
    assert client.get("/meetings/9999", headers=meeting_access[0]).status_code == 404
    assert (
        client.post(
            "/meetings/9999/tasks", headers=meeting_access[0], json={"title": "Task"}
        ).status_code
        == 404
    )
