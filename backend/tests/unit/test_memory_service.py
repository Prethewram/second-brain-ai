from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.models.memory import Memory
from app.models.user import User
from app.modules.memory.repository import MemoryRepository
from app.modules.memory.schemas import MemoryUpdate
from app.modules.memory.service import MemoryService
from app.services.ai.action_engine import ActionEngine
from app.ai.schemas.actions import Action


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
    return MemoryService(db_session)


@pytest.fixture
def memory(db_session, users):
    memory = Memory(
        user_id=users[0].id, content="Original", category="general", importance=1
    )
    db_session.add(memory)
    db_session.commit()
    return memory


def test_create_persists_defaults_and_trims_text(service, users, db_session):
    memory = service.create_memory(users[0].id, "  Likes Python  ")
    db_session.expire_all()
    stored = db_session.get(Memory, memory.id)
    assert (
        stored.user_id,
        stored.content,
        stored.category,
        stored.importance,
        stored.source,
    ) == (
        users[0].id,
        "Likes Python",
        "general",
        1,
        "chat",
    )


def test_get_returns_owned_memory(service, users, memory):
    assert service.get_memory(users[0].id, memory.id).content == "Original"


def test_update_persists_all_fields(service, users, memory, db_session):
    service.update_memory(
        users[0].id,
        memory.id,
        MemoryUpdate(
            content="  Updated  ",
            category=" WORK ",
            importance=5,
        ),
    )
    db_session.expire_all()
    stored = db_session.get(Memory, memory.id)
    assert (stored.content, stored.category, stored.importance) == (
        "Updated",
        "work",
        5,
    )


def test_delete_removes_owned_memory(service, users, memory, db_session):
    memory_id = memory.id
    service.delete_memory(users[0].id, memory_id)
    assert db_session.get(Memory, memory_id) is None


@pytest.mark.parametrize("operation", ["get", "update", "delete"])
def test_missing_memory_raises_not_found(service, users, operation):
    with pytest.raises(NotFoundException):
        if operation == "update":
            service.update_memory(
                users[0].id,
                999,
                MemoryUpdate(content="New", category="general", importance=1),
            )
        else:
            getattr(service, f"{operation}_memory")(users[0].id, 999)


@pytest.mark.parametrize("operation", ["get", "update", "delete"])
def test_other_users_cannot_access_or_mutate_memory(
    service, users, memory, db_session, operation
):
    with pytest.raises(UnauthorizedException):
        if operation == "update":
            service.update_memory(
                users[1].id,
                memory.id,
                MemoryUpdate(content="Stolen", category="general", importance=2),
            )
        else:
            getattr(service, f"{operation}_memory")(users[1].id, memory.id)
    db_session.expire_all()
    assert db_session.get(Memory, memory.id).content == "Original"


@pytest.mark.parametrize(
    "values",
    [
        {"content": "   "},
        {"content": None},
        {"category": " "},
        {"category": "x" * 101},
        {"importance": "high"},
        {"importance": True},
    ],
)
def test_invalid_create_does_not_persist(service, users, db_session, values):
    data = {"content": "Valid", "category": "general", "importance": 1}
    data.update(values)
    with pytest.raises(ValidationException):
        service.create_memory(users[0].id, **data)
    assert db_session.query(Memory).count() == 0


def test_invalid_update_leaves_session_and_database_unchanged(
    service, users, memory, db_session
):
    with pytest.raises(ValidationException):
        service.update_memory(
            users[0].id,
            memory.id,
            SimpleNamespace(
                content="New text",
                category=" ",
                importance=2,
            ),
        )
    assert memory.content == "Original"
    db_session.commit()
    db_session.expire_all()
    assert db_session.get(Memory, memory.id).content == "Original"


def test_list_and_context_retrieval_are_user_scoped_and_ordered(
    service, users, db_session
):
    now = datetime(2026, 1, 1)
    db_session.add_all(
        [
            Memory(user_id=users[0].id, content="Low", importance=1, created_at=now),
            Memory(
                user_id=users[0].id, content="Older high", importance=5, created_at=now
            ),
            Memory(
                user_id=users[0].id,
                content="Newer high",
                importance=5,
                created_at=now + timedelta(days=1),
            ),
            Memory(
                user_id=users[1].id, content="Private", importance=10, created_at=now
            ),
        ]
    )
    db_session.commit()
    assert [m.content for m in service.list_memories(users[0].id)] == [
        "Newer high",
        "Older high",
        "Low",
    ]
    assert [
        m.content for m in service.repository.get_top_memories(users[0].id, limit=1)
    ] == ["Newer high"]


def test_empty_list(service, users):
    assert service.list_memories(users[0].id) == []


def test_real_ai_memory_action_persists_through_service(users, db_session):
    result = ActionEngine(db_session).execute(
        users[0].id,
        [
            Action(
                type="memory.create",
                payload={"content": "  Remember this  "},
            )
        ],
    )
    assert result == {"executed": 1, "failed": 0, "skipped": 0}
    assert db_session.query(Memory).one().content == "Remember this"


def test_invalid_ai_memory_does_not_stop_next_action(users, db_session):
    result = ActionEngine(db_session).execute(
        users[0].id,
        [
            Action(type="memory.create", payload={"content": " "}),
            Action(type="memory.create", payload={"content": "Valid"}),
        ],
    )
    assert result == {"executed": 1, "failed": 1, "skipped": 0}
    assert db_session.query(Memory).one().content == "Valid"


def test_legacy_repository_calls_remain_supported(users, db_session):
    repository = MemoryRepository(db_session)
    memory = repository.create(users[0].id, "Legacy", "general", 1)
    repository.update(memory, "Updated", "work", 3)
    assert repository.get_by_id(memory.id).content == "Updated"
