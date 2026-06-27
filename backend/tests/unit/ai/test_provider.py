import pytest

from app.ai.errors import AITransientError
from app.ai.mock_provider import MockProvider
from app.ai.provider import AIProvider
from app.ai.schemas import GenerationRequest, ProviderResponse


def _request(prompt: str = "Hello there world", system: str | None = None):
    return GenerationRequest(prompt=prompt, system=system)


class TestMockProviderInterface:
    def test_is_an_ai_provider(self) -> None:
        assert isinstance(MockProvider(), AIProvider)

    def test_name_is_mock(self) -> None:
        assert MockProvider().name == "mock"

    def test_returns_provider_response(self) -> None:
        provider = MockProvider(default_response='{"hello": "world"}')
        result = provider.generate(_request())
        assert isinstance(result, ProviderResponse)
        assert result.text == '{"hello": "world"}'
        assert result.finish_reason == "stop"


class TestMockProviderResponses:
    def test_default_response(self) -> None:
        provider = MockProvider(default_response="canned")
        assert provider.generate(_request()).text == "canned"

    def test_queued_responses_in_order(self) -> None:
        provider = MockProvider(responses=["first", "second"])
        assert provider.generate(_request()).text == "first"
        assert provider.generate(_request()).text == "second"

    def test_handler_receives_request(self) -> None:
        provider = MockProvider(handler=lambda req: req.prompt.upper())
        assert provider.generate(_request("hi")).text == "HI"

    def test_uses_request_model_override(self) -> None:
        provider = MockProvider(model="mock-model")
        assert provider.generate(_request().model_copy(update={"model": "x"})).model == "x"


class TestMockProviderUsage:
    def test_counts_tokens_by_words(self) -> None:
        # prompt "Hello there world" -> 3 words; response "a b" -> 2 words.
        provider = MockProvider(default_response="a b")
        usage = provider.generate(_request("Hello there world")).usage
        assert usage.prompt_tokens == 3
        assert usage.completion_tokens == 2
        assert usage.total_tokens == 5

    def test_call_count_increments(self) -> None:
        provider = MockProvider()
        provider.generate(_request())
        provider.generate(_request())
        assert provider.calls == 2


class TestMockProviderFailures:
    def test_fails_then_succeeds(self) -> None:
        provider = MockProvider(fail_times=1, default_response="ok")
        with pytest.raises(AITransientError):
            provider.generate(_request())
        # Second call no longer fails.
        assert provider.generate(_request()).text == "ok"

    def test_custom_failure_exception(self) -> None:
        boom = AITransientError("boom")
        provider = MockProvider(fail_times=1, fail_exc=boom)
        with pytest.raises(AITransientError, match="boom"):
            provider.generate(_request())
