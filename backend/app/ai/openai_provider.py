import logging
from typing import TYPE_CHECKING, Any

from app.ai.errors import AIConfigurationError, AIProviderError, AITransientError
from app.ai.provider import AIProvider
from app.ai.schemas import GenerationRequest, ProviderResponse, TokenUsage

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    Production adapter for the OpenAI Chat Completions API.

    Deliberately built on httpx (lazily imported) rather than the OpenAI SDK,
    matching the Gmail integration's "thin HTTP client, no heavy SDK" approach.
    This keeps the dependency optional: the import only happens when an OpenAI
    call is actually made, so the platform — and the whole app — runs without
    httpx or any OpenAI credentials as long as the mock provider is used.

    An httpx.Client can be injected (http_client) so tests can drive it with a
    MockTransport and never touch the network.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        default_model: str,
        http_client: "httpx.Client | None" = None,
    ) -> None:
        if not api_key:
            raise AIConfigurationError("OpenAI API key is not configured")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._default_model = default_model
        self._http_client = http_client

    @property
    def name(self) -> str:
        return "openai"

    def _client(self) -> "httpx.Client":
        if self._http_client is not None:
            return self._http_client
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - defensive
            raise AIConfigurationError(
                "httpx is required to use the OpenAI provider"
            ) from exc
        return httpx.Client(base_url=self._base_url, timeout=self._timeout)

    def generate(self, request: GenerationRequest) -> ProviderResponse:
        import httpx

        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.max_output_tokens is not None:
            payload["max_tokens"] = request.max_output_tokens
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}

        client = self._client()
        try:
            response = client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise AITransientError(f"OpenAI request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            # Network-level failures are worth one more try.
            raise AITransientError(f"OpenAI request failed: {exc}") from exc

        self._raise_for_status(response)

        data = response.json()
        return self._to_response(data)

    @staticmethod
    def _raise_for_status(response: "httpx.Response") -> None:
        status = response.status_code
        if status < 400:
            return
        detail = OpenAIProvider._error_detail(response)
        # 429 (rate limit) and 5xx are transient; other 4xx are caller errors.
        if status == 429 or status >= 500:
            raise AITransientError(f"OpenAI returned {status}: {detail}")
        raise AIProviderError(f"OpenAI returned {status}: {detail}")

    @staticmethod
    def _error_detail(response: "httpx.Response") -> str:
        try:
            body = response.json()
            return str(body.get("error", {}).get("message") or body)
        except Exception:
            return response.text[:200]

    @staticmethod
    def _to_response(data: dict[str, Any]) -> ProviderResponse:
        try:
            choice = data["choices"][0]
            text = choice["message"]["content"] or ""
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                "OpenAI response was missing the expected choices/message fields"
            ) from exc

        usage_data = data.get("usage") or {}
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )
        return ProviderResponse(
            text=text,
            model=data.get("model", "unknown"),
            usage=usage,
            finish_reason=finish_reason,
            raw=data,
        )
