from unittest.mock import Mock

import pytest

from app.core.config import settings
from app.models.task import Task
from app.models.user import User
from app.modules.auth.security import create_access_token

PATH = "/dev/test-action-engine"


@pytest.fixture
def dev_users(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("first", "caller")
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


def test_development_endpoint_is_disabled_by_default(client, db_session):
    assert settings.ENABLE_DEV_ENDPOINTS is False
    assert client.post(PATH).status_code == 404
    assert db_session.query(Task).count() == 0


def test_enabled_endpoint_requires_authentication(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_DEV_ENDPOINTS", True)
    assert client.post(PATH).status_code == 401
    assert db_session.query(Task).count() == 0


def test_enabled_endpoint_creates_task_for_caller_not_user_one(
    client, db_session, dev_users, monkeypatch
):
    monkeypatch.setattr(settings, "ENABLE_DEV_ENDPOINTS", True)
    headers = {"Authorization": f"Bearer {create_access_token(dev_users[1].id)}"}
    response = client.post(PATH, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Task created"}
    task = db_session.query(Task).one()
    assert task.user_id == dev_users[1].id
    assert task.user_id != dev_users[0].id
    assert (task.title, task.priority, task.deadline) == (
        "Finish Backend",
        "high",
        "Tomorrow",
    )


def test_failed_action_does_not_report_success(client, dev_users, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_DEV_ENDPOINTS", True)
    engine = Mock()
    engine.execute.return_value = {"executed": 0, "failed": 1, "skipped": 0}
    monkeypatch.setattr("app.modules.dev.router.ActionEngine", lambda db: engine)
    headers = {"Authorization": f"Bearer {create_access_token(dev_users[1].id)}"}
    response = client.post(PATH, headers=headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "Test action failed"
