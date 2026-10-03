import json
from unittest.mock import Mock

import pytest

from app.models.memory import Memory
from app.models.user import User
from app.modules.auth.security import create_access_token


@pytest.fixture
def access(db_session):
    user = User(name="Test", email="test@example.com", password_hash="unused")
    db_session.add(user)
    db_session.commit()
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


@pytest.fixture
def ai(monkeypatch):
    client = Mock()
    client.chat.return_value = json.dumps(
        {"actions": [], "reply": {"text": "Analyzed"}}
    )
    monkeypatch.setattr("app.services.ai.analyzer.AIClient", lambda: client)
    return client


def test_unauthenticated_analysis_does_not_call_provider(client, ai):
    response = client.post("/ai/analyze", json={"message": "Hello"})
    assert response.status_code == 401
    ai.chat.assert_not_called()


def test_invalid_token_does_not_call_provider(client, ai):
    response = client.post(
        "/ai/analyze",
        headers={"Authorization": "Bearer invalid"},
        json={"message": "Hello"},
    )
    assert response.status_code == 401
    ai.chat.assert_not_called()


def test_authenticated_analysis_returns_supported_actions_without_executing_them(
    client, access, ai, db_session
):
    ai.chat.return_value = json.dumps(
        {
            "actions": [
                {"type": "memory.create", "payload": {"content": "Likes Python"}},
                {"type": "profile.update", "payload": {"skills": "Python"}},
                {"type": "unsupported", "payload": {}},
            ],
            "reply": {"text": "Analyzed"},
        }
    )
    response = client.post(
        "/ai/analyze", headers=access, json={"message": "I like Python"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "actions": [
            {"type": "memory.create", "payload": {"content": "Likes Python"}},
            {"type": "profile.update", "payload": {"skills": "Python"}},
        ],
        "reply": {"text": "Analyzed"},
    }
    assert ai.chat.call_args.args[0][-1] == {"role": "user", "content": "I like Python"}
    assert db_session.query(Memory).count() == 0


@pytest.mark.parametrize(
    "body", [{}, {"message": ""}, {"message": " \n "}, {"message": 123}]
)
def test_invalid_input_is_rejected_before_provider_call(client, access, ai, body):
    response = client.post("/ai/analyze", headers=access, json=body)
    assert response.status_code == 422
    ai.chat.assert_not_called()


def test_malformed_provider_json_preserves_existing_fallback(client, access, ai):
    ai.chat.return_value = "Not JSON"
    response = client.post("/ai/analyze", headers=access, json={"message": "Hello"})
    assert response.status_code == 200
    assert response.json() == {"actions": [], "reply": {"text": "Not JSON"}}
