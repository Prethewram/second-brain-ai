import pytest

from app.services.ai.registry import HandlerRegistry
from app.services.ai.handlers.memory_handler import MemoryHandler
from app.modules.notes.handler import NoteHandler
from app.modules.tasks.handler import TaskHandler
from app.modules.profile.handler import ProfileHandler


class DummyDB:
    pass


@pytest.fixture
def registry():

    return HandlerRegistry(DummyDB())


def test_memory_handler_registered(registry):

    handler = registry.get("memory.create")

    assert isinstance(
        handler,
        MemoryHandler,
    )


def test_note_handler_registered(registry):

    handler = registry.get("note.create")

    assert isinstance(
        handler,
        NoteHandler,
    )


def test_task_handler_registered(registry):

    handler = registry.get("task.create")

    assert isinstance(
        handler,
        TaskHandler,
    )


def test_profile_handler_registered(registry):

    handler = registry.get("profile.update")

    assert isinstance(
        handler,
        ProfileHandler,
    )


def test_unknown_handler_returns_none(registry):

    handler = registry.get("unknown.action")

    assert handler is None
