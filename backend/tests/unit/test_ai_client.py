from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import errors
from httpx import ConnectError

from app.ai.client import AIClient
from app.common.exceptions import AIProviderException


@pytest.fixture
def provider(monkeypatch):
    fake = Mock()
    monkeypatch.setattr("app.ai.client.genai.Client", lambda **kwargs: fake)
    return fake


@pytest.mark.parametrize(
    "code,status,expected",
    [
        (503, 503, "busy"),
        (429, 503, "usage limit"),
        (500, 503, "temporarily unavailable"),
        (403, 502, "configuration"),
        (404, 502, "configuration"),
    ],
)
def test_provider_failures_are_sanitized(provider, code, status, expected):
    provider.models.generate_content.side_effect = errors.APIError(
        code, {"error": {"message": "private key or request content", "code": code}}
    )
    with pytest.raises(AIProviderException) as caught:
        AIClient().chat([{"role": "user", "content": "Hello"}])
    assert caught.value.status_code == status
    assert expected in caught.value.message
    assert "private" not in caught.value.message


def test_connection_failure_is_reported_safely(provider):
    provider.models.generate_content.side_effect = ConnectError("private URL")
    with pytest.raises(AIProviderException, match="Cannot reach the AI provider"):
        AIClient().chat([])


@pytest.mark.parametrize("text", [None, "", "  "])
def test_empty_provider_reply_is_not_saved_as_success(provider, text):
    provider.models.generate_content.return_value = SimpleNamespace(text=text)
    with pytest.raises(AIProviderException, match="empty reply"):
        AIClient().chat([])


def test_valid_provider_reply_is_preserved(provider):
    provider.models.generate_content.return_value = SimpleNamespace(text="A reply")
    assert AIClient().chat([{"role": "user", "content": "Hello"}]) == "A reply"
