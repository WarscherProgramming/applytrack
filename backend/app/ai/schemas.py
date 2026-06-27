from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token counts for a single generation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def of(cls, prompt_tokens: int, completion_tokens: int) -> "TokenUsage":
        return cls(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )


class GenerationRequest(BaseModel):
    """
    A provider-agnostic generation request.

    Features build this (usually from a rendered prompt template) and hand it to
    the AIClient. It carries no provider-specific fields, so the same request
    works against the mock or any real adapter.
    """

    prompt: str
    system: str | None = None
    # None means "use the client's default model" (resolved in AIClient).
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, gt=0)
    # When True the provider is asked for strict JSON output (e.g. OpenAI's
    # response_format=json_object). Set automatically by generate_structured().
    json_mode: bool = False


class ProviderResponse(BaseModel):
    """The raw result an AIProvider returns from a single generate() call."""

    text: str
    model: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: str | None = None
    # Provider's untouched response body, kept for debugging/auditing.
    raw: dict[str, Any] | None = None


class AIResult(BaseModel):
    """
    The platform's enriched result returned to feature code.

    Adds the cross-cutting concerns the provider doesn't know about: which
    provider answered, measured latency, and estimated cost.
    """

    text: str
    provider: str
    model: str
    usage: TokenUsage
    latency_ms: int
    estimated_cost_usd: float | None = None


T = TypeVar("T", bound=BaseModel)


@dataclass
class StructuredResult(Generic[T]):
    """Pairs a parsed-and-validated model with the underlying AIResult.

    Returned by AIClient.generate_structured so callers get typed data plus the
    usage/latency/cost metadata in one object.
    """

    data: T
    result: AIResult
