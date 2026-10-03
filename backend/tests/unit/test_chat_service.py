from unittest.mock import Mock

import pytest

from app.ai.schemas.actions import Action, AnalysisResult
from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.models.conversation import Conversation
from app.models.memory import Memory
from app.models.message import Message
from app.models.user import User
from app.modules.chat.repository import ChatRepository
from app.modules.chat.service import ChatService


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
def dependencies():
    analyzer, orchestrator = Mock(), Mock()
    analyzer.analyze.return_value = AnalysisResult()
    orchestrator.generate_reply.return_value = "AI reply"
    return analyzer, orchestrator


@pytest.fixture
def service(db_session, dependencies):
    analyzer, orchestrator = dependencies
    return ChatService(db_session, analyzer=analyzer, orchestrator=orchestrator)


def test_new_chat_persists_owned_conversation_and_ordered_messages(
    service, users, db_session, dependencies
):
    result = service.chat(users[0].id, None, "Hello")
    assert result == {
        "conversation_id": result["conversation_id"],
        "response": "AI reply",
    }
    conversation = db_session.get(Conversation, result["conversation_id"])
    assert conversation.user_id == users[0].id
    assert conversation.title == "New Chat"
    assert [
        (m.role, m.content)
        for m in ChatRepository(db_session).get_messages(conversation.id)
    ] == [
        ("user", "Hello"),
        ("assistant", "AI reply"),
    ]
    dependencies[0].analyze.assert_called_once_with("Hello")
    assert dependencies[1].generate_reply.call_args.kwargs["user_id"] == users[0].id


def test_continuation_reuses_conversation_and_passes_ordered_history(
    service, users, db_session, dependencies
):
    first = service.chat(users[0].id, None, "First")
    result = service.chat(users[0].id, first["conversation_id"], "Second")
    assert result["conversation_id"] == first["conversation_id"]
    assert db_session.query(Conversation).count() == 1
    history = dependencies[1].generate_reply.call_args.kwargs["messages"]
    assert [(m.role, m.content) for m in history] == [
        ("user", "First"),
        ("assistant", "AI reply"),
        ("user", "Second"),
    ]
    assert db_session.query(Message).count() == 4


def test_foreign_conversation_is_rejected_before_any_ai_or_persistence(
    service, users, db_session, dependencies
):
    conversation = ChatRepository(db_session).create_conversation(users[0].id)
    with pytest.raises(UnauthorizedException):
        service.chat(users[1].id, conversation.id, "Intrusion")
    dependencies[0].analyze.assert_not_called()
    dependencies[1].generate_reply.assert_not_called()
    assert db_session.query(Message).count() == 0


def test_missing_conversation_has_no_side_effects(
    service, users, db_session, dependencies
):
    with pytest.raises(NotFoundException):
        service.chat(users[0].id, 999, "Hello")
    assert db_session.query(Conversation).count() == 0
    assert db_session.query(Message).count() == 0
    dependencies[0].analyze.assert_not_called()


@pytest.mark.parametrize("message", ["", " \n\t ", None, 123])
def test_invalid_message_has_no_side_effects(
    service, users, db_session, dependencies, message
):
    with pytest.raises(ValidationException):
        service.chat(users[0].id, None, message)
    assert db_session.query(Conversation).count() == 0
    dependencies[0].analyze.assert_not_called()


def test_actions_persist_before_reply_is_generated(
    service, users, db_session, dependencies
):
    dependencies[0].analyze.return_value = AnalysisResult(
        actions=[
            Action(type="memory.create", payload={"content": "Remember this"}),
        ]
    )

    def generate_reply(**kwargs):
        assert db_session.query(Memory).one().user_id == users[0].id
        return "Saved"

    dependencies[1].generate_reply.side_effect = generate_reply
    assert service.chat(users[0].id, None, "Remember this")["response"] == "Saved"


def test_failed_and_unknown_actions_do_not_prevent_reply(
    service, users, db_session, dependencies
):
    dependencies[0].analyze.return_value = AnalysisResult(
        actions=[
            Action(type="memory.create", payload={"content": " "}),
            Action(type="unknown.action"),
            Action(type="memory.create", payload={"content": "Valid"}),
        ]
    )
    assert service.chat(users[0].id, None, "Hello")["response"] == "AI reply"
    assert db_session.query(Memory).one().content == "Valid"


@pytest.mark.parametrize("failure_stage", ["analyzer", "reply"])
def test_provider_failure_keeps_user_message_without_fabricating_assistant_reply(
    service,
    users,
    db_session,
    dependencies,
    failure_stage,
):
    if failure_stage == "analyzer":
        dependencies[0].analyze.side_effect = RuntimeError("Provider unavailable")
    else:
        dependencies[1].generate_reply.side_effect = RuntimeError(
            "Provider unavailable"
        )
    with pytest.raises(RuntimeError, match="Provider unavailable"):
        service.chat(users[0].id, None, "Hello")
    assert [(m.role, m.content) for m in db_session.query(Message).all()] == [
        ("user", "Hello")
    ]
    if failure_stage == "analyzer":
        dependencies[1].generate_reply.assert_not_called()
