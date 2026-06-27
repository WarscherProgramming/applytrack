import logging
from collections.abc import Callable

from app.ai.errors import AITransientError
from app.ai.provider import AIProvider
from app.ai.schemas import GenerationRequest, ProviderResponse, TokenUsage

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (word count) — enough to exercise usage tracking."""
    return len(text.split())


class MockProvider(AIProvider):
    """
    Deterministic provider for local development and tests.

    No network, no credentials. It returns canned text so the whole pipeline
    (render → generate → parse → track usage) works offline, and it can simulate
    transient failures so retry behaviour is testable without a real backend.

    Construction options:
      default_response: returned when no queue/handler is set.
      responses:        a queue; each call pops the next item.
      handler:          a callable(request) -> str for dynamic responses.
      fail_times:       raise a transient error this many times before succeeding
                        (drives retry tests).
    """

    def __init__(
        self,
        *,
        default_response: str = '{"ok": true}',
        responses: list[str] | None = None,
        handler: Callable[[GenerationRequest], str] | None = None,
        model: str = "mock-model",
        fail_times: int = 0,
        fail_exc: Exception | None = None,
    ) -> None:
        self._default_response = default_response
        self._responses = list(responses) if responses else []
        self._handler = handler
        self._model = model
        self._fail_remaining = fail_times
        self._fail_exc = fail_exc
        # Number of generate() calls served — useful for assertions in tests.
        self.calls = 0

    @property
    def name(self) -> str:
        return "mock"

    def generate(self, request: GenerationRequest) -> ProviderResponse:
        self.calls += 1

        if self._fail_remaining > 0:
            self._fail_remaining -= 1
            raise self._fail_exc or AITransientError("Simulated transient failure")

        if self._handler is not None:
            text = self._handler(request)
        elif self._responses:
            text = self._responses.pop(0)
        else:
            text = self._default_response

        prompt_text = f"{request.system or ''} {request.prompt}"
        usage = TokenUsage.of(_estimate_tokens(prompt_text), _estimate_tokens(text))
        return ProviderResponse(
            text=text,
            model=request.model or self._model,
            usage=usage,
            finish_reason="stop",
        )
