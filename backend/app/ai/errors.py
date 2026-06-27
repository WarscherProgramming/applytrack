from typing import ClassVar

from app.exceptions.http import AppError


class AIError(AppError):
    """
    Base for every AI-platform error.

    Subclasses AppError so the global exception handler renders them as JSON
    without the platform knowing anything about HTTP. Default status is 502
    (Bad Gateway): an AI failure is usually an upstream-provider problem, not a
    fault in our own request handling.
    """

    status_code: ClassVar[int] = 502


class AIConfigurationError(AIError):
    """The selected provider is missing required configuration (e.g. API key).

    503 Service Unavailable — the feature is temporarily unusable until
    configured, rather than a gateway error.
    """

    status_code: ClassVar[int] = 503


class AIProviderError(AIError):
    """A provider call failed in a way that should NOT be retried.

    Examples: authentication failure, malformed request (4xx other than 429).
    """

    # Drives the retry policy. Non-transient errors are surfaced immediately.
    retryable: ClassVar[bool] = False


class AITransientError(AIProviderError):
    """A provider call failed transiently and is safe to retry.

    Examples: rate limiting (429), timeouts, provider 5xx responses.
    """

    retryable: ClassVar[bool] = True


class AIResponseError(AIError):
    """The provider returned a response we could not use.

    Invalid JSON or a payload that fails schema validation. Never retried —
    retrying an identical request would return the same unusable output.
    """


class PromptRenderError(AIError):
    """A prompt template could not be rendered (missing/invalid variables).

    500 — this is a programming error in how a feature called the platform,
    surfaced before any provider call is made.
    """

    status_code: ClassVar[int] = 500
