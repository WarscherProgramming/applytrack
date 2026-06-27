"""
ApplyTrack AI platform.

A small, provider-agnostic layer that future AI features (Resume Match, Cover
Letter AI, Interview Prep, Analytics AI) all consume. Feature code depends only
on the public surface re-exported here — never on a concrete provider, the retry
policy, or the usage table — so swapping or adding providers never touches a
feature service.

Typical use from a feature service:

    from app.ai import get_ai_client, GenerationRequest, render_template

    prompt = render_template("resume_match.v1", {"resume": ..., "job": ...})
    client = get_ai_client()
    result = client.generate_structured(
        GenerationRequest(system=prompt.system, prompt=prompt.user),
        ResumeMatchResult,
        db=db,
        feature="resume_match",
    )
"""

from functools import lru_cache

from app.ai.client import AIClient
from app.ai.errors import (
    AIConfigurationError,
    AIError,
    AIProviderError,
    AIResponseError,
    AITransientError,
    PromptRenderError,
)
from app.ai.mock_provider import MockProvider
from app.ai.prompt_templates import (
    PromptTemplate,
    RenderedPrompt,
    get_template,
    register_template,
    render_template,
)
from app.ai.provider import AIProvider
from app.ai.schemas import (
    AIResult,
    GenerationRequest,
    ProviderResponse,
    StructuredResult,
    TokenUsage,
)
from app.core.config import settings

__all__ = [
    "AIClient",
    "AIProvider",
    "MockProvider",
    "GenerationRequest",
    "ProviderResponse",
    "AIResult",
    "StructuredResult",
    "TokenUsage",
    "PromptTemplate",
    "RenderedPrompt",
    "render_template",
    "register_template",
    "get_template",
    "AIError",
    "AIConfigurationError",
    "AIProviderError",
    "AITransientError",
    "AIResponseError",
    "PromptRenderError",
    "get_ai_provider",
    "get_ai_client",
]


def get_ai_provider() -> AIProvider:
    """
    Build the configured provider.

    Returns OpenAIProvider only when AI_PROVIDER=openai AND a key is present;
    otherwise the MockProvider. This guarantees the app runs locally with no
    credentials and never makes an accidental external call.
    """
    if settings.ai_active_provider == "openai":
        # Imported lazily so the optional httpx/OpenAI path is never loaded in
        # the default mock configuration.
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            timeout=settings.AI_REQUEST_TIMEOUT,
            default_model=settings.AI_MODEL,
        )
    return MockProvider()


@lru_cache
def get_ai_client() -> AIClient:
    """Application-wide AIClient (cached). Tests construct AIClient directly."""
    return AIClient(
        provider=get_ai_provider(),
        default_model=settings.AI_MODEL,
        max_retries=settings.AI_MAX_RETRIES,
    )
