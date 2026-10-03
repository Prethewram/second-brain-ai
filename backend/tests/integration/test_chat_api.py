import json
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.models.conversation import Conversation
from app.models.memory import Memory
from app.models.message import Message
from app.models.user import User
from app.modules.auth.security import create_access_token
from app.modules.chat.repository import ChatRepository


@pytest.fixture
def chat_access(db_session):
    users = [
        User(name=name, email=f"{name}@example.com", password_hash="unused")
        for name in ("owner", "other")
    ]
    db_session.add_all(users)
    db_session.commit()
    return users, [
        {"Authorization": f"Bearer {create_access_token(user.id)}"} for user in users
    ]


@pytest.fixture
def fake_ai(monkeypatch):
    analyzer_ai, reply_ai = Mock(), Mock()
    analyzer_ai.chat.return_value = json.dumps({"actions": []})
    reply_ai.chat.return_value = "AI reply"
    monkeypatch.setattr("app.services.ai.analyzer.AIClient", lambda: analyzer_ai)
    monkeypatch.setattr("app.services.ai.orchestrator.AIClient", lambda: reply_ai)
    return analyzer_ai, reply_ai


def test_new_chat_and_continuation_persist_and_use_ordered_history(
    client, chat_access, fake_ai, db_session
):
    users, headers = chat_access
    response = client.post("/chat", headers=headers[0], json={"message": "First"})
    assert response.status_code == 200
    data = response.json()
    assert data == {"conversation_id": data["conversation_id"], "response": "AI reply"}
    assert db_session.get(Conversation, data["conversation_id"]).user_id == users[0].id
    response = client.post(
        "/chat",
        headers=headers[0],
        json={
            "conversation_id": data["conversation_id"],
            "message": "Second",
        },
    )
    assert response.status_code == 200
    assert response.json()["conversation_id"] == data["conversation_id"]
    assert db_session.query(Conversation).count() == 1
    history = ChatRepository(db_session).get_messages(data["conversation_id"])
    assert [(m.role, m.content) for m in history] == [
        ("user", "First"),
        ("assistant", "AI reply"),
        ("user", "Second"),
        ("assistant", "AI reply"),
    ]
    prompt = fake_ai[1].chat.call_args.args[0]
    assert prompt[-3:] == [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "AI reply"},
        {"role": "user", "content": "Second"},
    ]


def test_foreign_conversation_is_rejected_without_ai_calls_or_changes(
    client, chat_access, fake_ai, db_session
):
    users, headers = chat_access
    repository = ChatRepository(db_session)
    conversation = repository.create_conversation(users[0].id)
    repository.add_message(conversation.id, "user", "Private history")
    response = client.post(
        "/chat",
        headers=headers[1],
        json={
            "conversation_id": conversation.id,
            "message": "Intrusion",
        },
    )
    assert response.status_code == 401
    assert response.json()["success"] is False
    fake_ai[0].chat.assert_not_called()
    fake_ai[1].chat.assert_not_called()
    assert [(m.role, m.content) for m in repository.get_messages(conversation.id)] == [
        ("user", "Private history")
    ]


def test_missing_conversation_returns_404_without_ai_calls(
    client, chat_access, fake_ai, db_session
):
    _, headers = chat_access
    response = client.post(
        "/chat", headers=headers[0], json={"conversation_id": 999, "message": "Hello"}
    )
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert db_session.query(Message).count() == 0
    fake_ai[0].chat.assert_not_called()


def test_authentication_required(client, fake_ai):
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 401
    fake_ai[0].chat.assert_not_called()


@pytest.mark.parametrize(
    "body,status",
    [
        ({"message": " "}, 400),
        ({"message": ""}, 400),
        ({}, 422),
        ({"message": 123}, 422),
        ({"message": "Hello", "conversation_id": "invalid"}, 422),
    ],
)
def test_invalid_request_does_not_persist_or_call_ai(
    client, chat_access, fake_ai, db_session, body, status
):
    _, headers = chat_access
    response = client.post("/chat", headers=headers[0], json=body)
    assert response.status_code == status
    assert db_session.query(Conversation).count() == 0
    fake_ai[0].chat.assert_not_called()


def test_action_result_enters_reply_context_without_other_users_memories(
    client, chat_access, fake_ai, db_session
):
    users, headers = chat_access
    db_session.add(
        Memory(user_id=users[1].id, content="Other user's secret", importance=10)
    )
    db_session.commit()
    fake_ai[0].chat.return_value = json.dumps(
        {
            "actions": [
                {"type": "memory.create", "payload": {"content": "Likes Python"}},
            ]
        }
    )
    response = client.post(
        "/chat", headers=headers[0], json={"message": "Remember that I like Python"}
    )
    assert response.status_code == 200
    assert (
        db_session.query(Memory).filter_by(user_id=users[0].id).one().content
        == "Likes Python"
    )
    prompt = fake_ai[1].chat.call_args.args[0]
    context = "\n".join(
        message["content"] for message in prompt if message["role"] == "system"
    )
    assert "Likes Python" in context
    assert "Other user's secret" not in context


def test_invalid_analyzer_json_still_allows_reply_without_actions(
    client, chat_access, fake_ai, db_session
):
    _, headers = chat_access
    fake_ai[0].chat.return_value = "Not JSON"
    response = client.post("/chat", headers=headers[0], json={"message": "Hello"})
    assert response.status_code == 200
    assert response.json()["response"] == "AI reply"
    assert db_session.query(Memory).count() == 0


@pytest.mark.parametrize("stage", [0, 1])
def test_provider_failure_returns_generic_500_and_keeps_only_user_message(
    client,
    chat_access,
    fake_ai,
    db_session,
    stage,
):
    from app.main import app

    _, headers = chat_access
    fake_ai[stage].chat.side_effect = RuntimeError("Private provider error")
    # Keep the active client's database override, but inspect handled 500 responses.
    with TestClient(app, raise_server_exceptions=False) as error_client:
        response = error_client.post(
            "/chat", headers=headers[0], json={"message": "Hello"}
        )
    assert response.status_code == 500
    assert response.json()["message"] == "Internal Server Error"
    assert "Private provider error" not in response.text
    assert [(m.role, m.content) for m in db_session.query(Message).all()] == [
        ("user", "Hello")
    ]
