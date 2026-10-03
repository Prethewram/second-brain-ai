from datetime import datetime, timedelta

import pytest

from app.ai.schemas.actions import Action
from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.models.task import Task
from app.models.user import User
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.service import TaskService
from app.services.ai.action_engine import ActionEngine


@pytest.fixture
def users(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


@pytest.fixture
def service(db_session):
    return TaskService(db_session)


@pytest.fixture
def task(service, users):
    return service.create_task(
        users[0].id, "Original", description="Details", deadline="Tomorrow"
    )


def test_create_defaults_and_normalization(service, users, db_session):
    task = service.create_task(users[0].id, " Work ", priority=" HIGH ")
    db_session.expire_all()
    stored = db_session.get(Task, task.id)
    assert (
        stored.title,
        stored.priority,
        stored.completed,
        stored.description,
        stored.deadline,
    ) == (
        "Work",
        "high",
        False,
        None,
        None,
    )


def test_unknown_creation_priority_keeps_existing_medium_fallback(service, users):
    assert (
        service.create_task(users[0].id, "Work", priority="urgent").priority == "medium"
    )


def test_get_and_update_all_fields(service, users, task, db_session):
    assert service.get_task(users[0].id, task.id).title == "Original"
    service.update_task(
        users[0].id,
        task.id,
        title=" Changed ",
        description="New details",
        priority=" LOW ",
        deadline="Friday",
    )
    db_session.expire_all()
    stored = db_session.get(Task, task.id)
    assert (stored.title, stored.description, stored.priority, stored.deadline) == (
        "Changed",
        "New details",
        "low",
        "Friday",
    )


def test_partial_update_and_explicit_nulls(service, users, task, db_session):
    service.update_task(
        users[0].id, task.id, title=None, priority=None, description=None, deadline=None
    )
    db_session.expire_all()
    stored = db_session.get(Task, task.id)
    assert (stored.title, stored.priority, stored.description, stored.deadline) == (
        "Original",
        "medium",
        None,
        None,
    )


def test_completion_is_persisted_and_idempotent(service, users, task, db_session):
    service.complete_task(users[0].id, task.id)
    service.complete_task(users[0].id, task.id)
    db_session.expire_all()
    assert db_session.get(Task, task.id).completed is True
    assert service.repository.get_active_tasks(users[0].id) == []


def test_delete_removes_task(service, users, task, db_session):
    task_id = task.id
    service.delete_task(users[0].id, task_id)
    assert db_session.get(Task, task_id) is None


@pytest.mark.parametrize("operation", ["get", "update", "complete", "delete"])
def test_missing_task(service, users, operation):
    with pytest.raises(NotFoundException):
        getattr(service, f"{operation}_task")(users[0].id, 999)


@pytest.mark.parametrize("operation", ["get", "update", "complete", "delete"])
def test_ownership(service, users, task, db_session, operation):
    with pytest.raises(UnauthorizedException):
        getattr(service, f"{operation}_task")(users[1].id, task.id)
    db_session.expire_all()
    assert db_session.get(Task, task.id).completed is False


@pytest.mark.parametrize(
    "data",
    [
        {"title": " "},
        {"title": None},
        {"title": "x" * 256},
        {"priority": None},
        {"description": 12},
        {"deadline": 12},
        {"deadline": "x" * 101},
    ],
)
def test_invalid_create_does_not_persist(service, users, db_session, data):
    values = {"title": "Valid"}
    values.update(data)
    with pytest.raises(ValidationException):
        service.create_task(users[0].id, **values)
    assert db_session.query(Task).count() == 0


@pytest.mark.parametrize(
    "data",
    [
        {"priority": "urgent"},
        {"priority": 12},
        {"title": " "},
        {"title": "x" * 256},
        {"description": 12},
        {"deadline": "x" * 101},
    ],
)
def test_invalid_update_leaves_no_partial_mutation(
    service, users, task, db_session, data
):
    values = {"title": "Changed", "description": "Changed"}
    values.update(data)
    with pytest.raises(ValidationException):
        service.update_task(users[0].id, task.id, **values)
    assert task.title == "Original"
    db_session.commit()
    db_session.expire_all()
    assert db_session.get(Task, task.id).description == "Details"


def test_lists_are_scoped_ordered_and_active_limit_is_applied(
    service, users, db_session
):
    now = datetime(2026, 1, 1)
    db_session.add_all(
        [
            Task(user_id=users[0].id, title="Old", created_at=now),
            Task(user_id=users[0].id, title="New", created_at=now + timedelta(days=1)),
            Task(
                user_id=users[0].id,
                title="Done",
                completed=True,
                created_at=now + timedelta(days=2),
            ),
            Task(user_id=users[1].id, title="Private"),
        ]
    )
    db_session.commit()
    assert [t.title for t in service.list_tasks(users[0].id)] == ["Done", "New", "Old"]
    assert [
        t.title for t in service.repository.get_active_tasks(users[0].id, limit=1)
    ] == ["New"]


def test_real_ai_action_persists_and_continues_after_validation_failure(
    users, db_session
):
    result = ActionEngine(db_session).execute(
        users[0].id,
        [
            Action(type="task.create", payload={"title": " "}),
            Action(
                type="task.create", payload={"title": " Work ", "deadline": "Tomorrow"}
            ),
        ],
    )
    assert result == {"executed": 1, "failed": 1, "skipped": 0}
    stored = db_session.query(Task).one()
    assert (stored.title, stored.deadline) == ("Work", "Tomorrow")


def test_legacy_repository_id_calls_remain_supported(users, db_session):
    repository = TaskRepository(db_session)
    task = repository.create(users[0].id, "Legacy")
    assert repository.get(task_id=task.id).title == "Legacy"
    assert repository.complete(task_id=task.id).completed is True
    assert repository.delete(task_id=task.id) is True
    assert repository.complete(task_id=999) is None
    assert repository.delete(task_id=999) is False
