"""OpenAIProvider adapter tests.

These exercise the adapter with an httpx MockTransport — no real network calls
are ever made — verifying request handling, response parsing, and the mapping of
HTTP status codes to the platform's transient/non-transient error types.
"""

import httpx
import pytest

from app.ai.errors import AIConfigurationError, AIProviderError, AITransientError
from app.ai.openai_provider import OpenAIProvider
from app.ai.schemas import GenerationRequest


def _provider_with(handler) -> OpenAIProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://test")
    return OpenAIProvider(
        api_key="sk-test",
        base_url="http://test",
        timeout=5.0,
        default_model="gpt-4o-mini",
        http_client=client,
    )


_OK_BODY = {
    "model": "gpt-4o-mini",
    "choices": [{"message": {"content": '{"ok": true}'}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 11, "completion_tokens": 3, "total_tokens": 14},
}


class TestConfiguration:
    def test_missing_api_key_raises(self) -> None:
        with pytest.raises(AIConfigurationError):
            OpenAIProvider(
                api_key="",
                base_url="http://test",
                timeout=5.0,
                default_model="gpt-4o-mini",
            )

    def test_name_is_openai(self) -> None:
        assert _provider_with(lambda r: httpx.Response(200, json=_OK_BODY)).name == "openai"


class TestSuccessfulGeneration:
    def test_parses_response(self) -> None:
        provider = _provider_with(lambda r: httpx.Response(200, json=_OK_BODY))
        result = provider.generate(GenerationRequest(prompt="hi"))
        assert result.text == '{"ok": true}'
        assert result.model == "gpt-4o-mini"
        assert result.usage.total_tokens == 14
        assert result.finish_reason == "stop"

    def test_sends_system_and_json_mode(self) -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            import json

            captured.update(json.loads(request.content))
            return httpx.Response(200, json=_OK_BODY)

        provider = _provider_with(handler)
        provider.generate(
            GenerationRequest(prompt="user text", system="be terse", json_mode=True)
        )

        assert captured["messages"][0] == {"role": "system", "content": "be terse"}
        assert captured["messages"][1] == {"role": "user", "content": "user text"}
        assert captured["response_format"] == {"type": "json_object"}
        assert captured["model"] == "gpt-4o-mini"


class TestErrorMapping:
    def test_429_is_transient(self) -> None:
        provider = _provider_with(
            lambda r: httpx.Response(429, json={"error": {"message": "slow down"}})
        )
        with pytest.raises(AITransientError):
            provider.generate(GenerationRequest(prompt="hi"))

    def test_500_is_transient(self) -> None:
        provider = _provider_with(lambda r: httpx.Response(503, text="upstream"))
        with pytest.raises(AITransientError):
            provider.generate(GenerationRequest(prompt="hi"))

    def test_400_is_non_transient(self) -> None:
        provider = _provider_with(
            lambda r: httpx.Response(400, json={"error": {"message": "bad request"}})
        )
        with pytest.raises(AIProviderError) as exc_info:
            provider.generate(GenerationRequest(prompt="hi"))
        # Must be the non-transient base type, not the transient subclass.
        assert not isinstance(exc_info.value, AITransientError)

    def test_401_is_non_transient(self) -> None:
        provider = _provider_with(lambda r: httpx.Response(401, text="unauthorized"))
        with pytest.raises(AIProviderError):
            provider.generate(GenerationRequest(prompt="hi"))

    def test_timeout_is_transient(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        provider = _provider_with(handler)
        with pytest.raises(AITransientError):
            provider.generate(GenerationRequest(prompt="hi"))

    def test_malformed_body_is_non_transient(self) -> None:
        provider = _provider_with(lambda r: httpx.Response(200, json={"unexpected": 1}))
        with pytest.raises(AIProviderError):
            provider.generate(GenerationRequest(prompt="hi"))
