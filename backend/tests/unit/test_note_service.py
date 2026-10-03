from datetime import datetime, timedelta

import pytest

from app.ai.schemas.actions import Action
from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.models.notes import Note
from app.models.user import User
from app.modules.notes.repository import NoteRepository
from app.modules.notes.service import NoteService
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
    return NoteService(db_session)


@pytest.fixture
def note(service, users):
    return service.create_note(users[0].id, "Original", "Original content")


def test_create_normalizes_text_and_persists_defaults(service, users, db_session):
    note = service.create_note(users[0].id, "  Idea  ", "  Details  ", " WORK ")
    db_session.expire_all()
    stored = db_session.get(Note, note.id)
    assert (
        stored.title,
        stored.content,
        stored.category,
        stored.source,
        stored.is_archived,
    ) == (
        "Idea",
        "Details",
        "work",
        "manual",
        False,
    )
    assert stored.user_id == users[0].id


def test_get_and_partial_update_persist_without_changing_other_fields(
    service, users, note, db_session
):
    assert service.get_note(users[0].id, note.id).title == "Original"
    service.update_note(users[0].id, note.id, content="  New content  ")
    db_session.expire_all()
    stored = db_session.get(Note, note.id)
    assert (stored.title, stored.content, stored.category) == (
        "Original",
        "New content",
        "general",
    )


def test_update_all_text_fields(service, users, note, db_session):
    service.update_note(
        users[0].id, note.id, title=" New ", content=" New text ", category=" WORK "
    )
    db_session.expire_all()
    stored = db_session.get(Note, note.id)
    assert (stored.title, stored.content, stored.category) == (
        "New",
        "New text",
        "work",
    )


def test_null_patch_fields_preserve_values(service, users, note):
    service.update_note(
        users[0].id, note.id, title=None, content=None, category=None, is_archived=None
    )
    assert (note.title, note.content, note.category, note.is_archived) == (
        "Original",
        "Original content",
        "general",
        False,
    )


def test_archive_hides_note_but_preserves_direct_access_and_can_be_reversed(
    service, users, note, db_session
):
    service.archive_note(users[0].id, note.id)
    db_session.expire_all()
    assert service.list_notes(users[0].id) == []
    assert service.get_note(users[0].id, note.id).is_archived is True
    service.update_note(users[0].id, note.id, is_archived=False)
    db_session.expire_all()
    assert [n.id for n in service.list_notes(users[0].id)] == [note.id]


def test_delete_removes_note(service, users, note, db_session):
    note_id = note.id
    service.delete_note(users[0].id, note_id)
    assert db_session.get(Note, note_id) is None


@pytest.mark.parametrize("operation", ["get", "update", "archive", "delete"])
def test_missing_note_raises_not_found(service, users, operation):
    with pytest.raises(NotFoundException):
        getattr(service, f"{operation}_note")(users[0].id, 999)


@pytest.mark.parametrize("operation", ["get", "update", "archive", "delete"])
def test_other_users_cannot_access_or_mutate_note(
    service, users, note, db_session, operation
):
    with pytest.raises(UnauthorizedException):
        getattr(service, f"{operation}_note")(users[1].id, note.id)
    db_session.expire_all()
    stored = db_session.get(Note, note.id)
    assert stored.title == "Original"
    assert stored.is_archived is False


@pytest.mark.parametrize(
    "values",
    [
        {"title": " "},
        {"content": " "},
        {"title": None},
        {"content": 123},
        {"title": "x" * 256},
        {"category": " "},
        {"category": "x" * 101},
        {"category": None},
        {"source": " "},
        {"source": "x" * 51},
    ],
)
def test_invalid_creation_does_not_persist(service, users, db_session, values):
    data = {"title": "Valid", "content": "Valid"}
    data.update(values)
    with pytest.raises(ValidationException):
        service.create_note(users[0].id, **data)
    assert db_session.query(Note).count() == 0


@pytest.mark.parametrize(
    "values",
    [
        {"content": " "},
        {"category": " "},
        {"title": "x" * 256},
        {"category": "x" * 101},
        {"content": 123},
        {"is_archived": "yes"},
    ],
)
def test_invalid_update_does_not_mutate_or_leak_into_a_later_commit(
    service, users, note, db_session, values
):
    data = {"title": "Changed", "content": "New content"}
    data.update(values)
    with pytest.raises(ValidationException):
        service.update_note(users[0].id, note.id, **data)
    assert note.title == "Original"
    db_session.commit()
    db_session.expire_all()
    assert db_session.get(Note, note.id).content == "Original content"


def test_list_is_user_scoped_excludes_archived_and_orders_newest_first(
    service, users, db_session
):
    now = datetime(2026, 1, 1)
    db_session.add_all(
        [
            Note(user_id=users[0].id, title="Older", content="Text", created_at=now),
            Note(
                user_id=users[0].id,
                title="Newer",
                content="Text",
                created_at=now + timedelta(days=1),
            ),
            Note(
                user_id=users[0].id, title="Archived", content="Text", is_archived=True
            ),
            Note(user_id=users[1].id, title="Private", content="Text"),
        ]
    )
    db_session.commit()
    assert [n.title for n in service.list_notes(users[0].id)] == ["Newer", "Older"]


def test_ai_note_action_validates_and_persists_ai_source(users, db_session):
    result = ActionEngine(db_session).execute(
        users[0].id,
        [
            Action(type="note.create", payload={"title": "Bad", "content": " "}),
            Action(
                type="note.create", payload={"title": " Idea ", "content": " Details "}
            ),
        ],
    )
    assert result == {"executed": 1, "failed": 1, "skipped": 0}
    stored = db_session.query(Note).one()
    assert (stored.title, stored.content, stored.source) == ("Idea", "Details", "ai")


def test_legacy_repository_positional_create_remains_supported(users, db_session):
    repository = NoteRepository(db_session)
    note = repository.create(users[0].id, "Title", "Content", "work", "manual")
    assert repository.get(note_id=note.id).content == "Content"
