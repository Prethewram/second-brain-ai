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


def test_busy_primary_uses_fallback_without_replaying_prompt(provider, monkeypatch):
    monkeypatch.setattr("app.ai.client.settings.GEMINI_MODEL", "primary")
    monkeypatch.setattr("app.ai.client.settings.GEMINI_FALLBACK_MODEL", "fallback")
    provider.models.generate_content.side_effect = [
        errors.APIError(503, {"error": {"message": "Busy", "code": 503}}),
        SimpleNamespace(text="Fallback reply"),
    ]
    assert AIClient().chat([{"role": "user", "content": "Hello"}]) == "Fallback reply"
    calls = provider.models.generate_content.call_args_list
    assert [call.kwargs["model"] for call in calls] == ["primary", "fallback"]
    assert calls[0].kwargs["contents"] == calls[1].kwargs["contents"]


@pytest.mark.parametrize("code", [400, 401, 403, 404, 429])
def test_configuration_and_quota_errors_do_not_switch_models(provider, code):
    provider.models.generate_content.side_effect = errors.APIError(
        code, {"error": {"message": "Rejected", "code": code}}
    )
    with pytest.raises(AIProviderException):
        AIClient().chat([])
    assert provider.models.generate_content.call_count == 1


@pytest.mark.parametrize("fallback", ["", "primary"])
def test_disabled_or_identical_fallback_is_not_called(provider, monkeypatch, fallback):
    monkeypatch.setattr("app.ai.client.settings.GEMINI_MODEL", "primary")
    monkeypatch.setattr("app.ai.client.settings.GEMINI_FALLBACK_MODEL", fallback)
    provider.models.generate_content.side_effect = errors.APIError(
        503, {"error": {"message": "Busy", "code": 503}}
    )
    with pytest.raises(AIProviderException):
        AIClient().chat([])
    assert provider.models.generate_content.call_count == 1
