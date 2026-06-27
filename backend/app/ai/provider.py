from abc import ABC, abstractmethod

from app.ai.schemas import GenerationRequest, ProviderResponse


class AIProvider(ABC):
    """
    The single seam between the platform and any concrete LLM backend.

    Adapters (MockProvider, OpenAIProvider, and future Anthropic/etc.) implement
    this interface. Everything above it — the client, prompt rendering, parsing,
    retries, usage tracking — is provider-agnostic, so no provider-specific code
    ever leaks into feature services.

    Implementations must be synchronous to match the codebase's sync SQLAlchemy
    request model, and must raise app.ai.errors types (AITransientError for
    retryable failures, AIProviderError otherwise).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier persisted in usage records (e.g. 'openai')."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> ProviderResponse:
        """Produce a completion for `request`. Raises app.ai.errors on failure."""
