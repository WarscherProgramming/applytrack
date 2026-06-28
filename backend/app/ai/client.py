import logging
import time
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.errors import AIError
from app.ai.provider import AIProvider
from app.ai.response_parser import parse_model
from app.ai.retry import retry_call
from app.ai.schemas import (
    AIResult,
    GenerationRequest,
    StructuredResult,
    T,
    TokenUsage,
)
from app.ai.usage_tracker import UsageTracker, estimate_cost

logger = logging.getLogger(__name__)


class AIClient:
    """
    The single entry point feature services use for AI.

    It composes the cross-cutting concerns around a provider: model defaulting,
    retries, latency measurement, cost estimation, and usage persistence. Feature
    code never touches a provider, the retry policy, or the usage table directly —
    it builds a GenerationRequest (usually from a prompt template) and calls
    generate() / generate_structured().
    """

    def __init__(
        self,
        provider: AIProvider,
        *,
        default_model: str,
        max_retries: int = 2,
        tracker: UsageTracker | None = None,
    ) -> None:
        self.provider = provider
        self.default_model = default_model
        # attempts = retries + 1
        self.max_attempts = max_retries + 1
        self.tracker = tracker or UsageTracker()

    def generate(
        self,
        request: GenerationRequest,
        *,
        db: Session | None = None,
        feature: str | None = None,
        user_id: UUID | None = None,
    ) -> AIResult:
        """Run a generation through retries, then track and return the result.

        Usage is persisted only when a `db` session is supplied (it always is in
        request-handling code; pure unit tests may omit it). Both successful and
        terminally-failed calls are recorded.
        """
        model = request.model or self.default_model
        effective = request.model_copy(update={"model": model})

        start = time.perf_counter()
        try:
            response = retry_call(
                lambda: self.provider.generate(effective),
                max_attempts=self.max_attempts,
            )
        except AIError:
            latency_ms = self._elapsed_ms(start)
            if db is not None:
                self.tracker.record(
                    db,
                    provider=self.provider.name,
                    model=model,
                    feature=feature,
                    user_id=user_id,
                    usage=TokenUsage(),
                    latency_ms=latency_ms,
                    success=False,
                )
            raise

        latency_ms = self._elapsed_ms(start)
        cost: Decimal | None = estimate_cost(response.model, response.usage)

        if db is not None:
            self.tracker.record(
                db,
                provider=self.provider.name,
                model=response.model,
                feature=feature,
                user_id=user_id,
                usage=response.usage,
                latency_ms=latency_ms,
                success=True,
                estimated_cost_usd=cost,
            )

        return AIResult(
            text=response.text,
            provider=self.provider.name,
            model=response.model,
            usage=response.usage,
            latency_ms=latency_ms,
            estimated_cost_usd=float(cost) if cost is not None else None,
        )

    def generate_structured(
        self,
        request: GenerationRequest,
        schema: type[T],
        *,
        db: Session | None = None,
        feature: str | None = None,
        user_id: UUID | None = None,
    ) -> StructuredResult[T]:
        """Generate, then parse+validate the output into `schema`.

        Forces JSON mode on the request. Usage is tracked for the call itself; a
        parse/schema failure surfaces as AIResponseError after usage is recorded
        (the tokens were genuinely consumed).
        """
        json_request = request.model_copy(update={"json_mode": True})
        result = self.generate(json_request, db=db, feature=feature, user_id=user_id)
        data = parse_model(result.text, schema)
        return StructuredResult(data=data, result=result)

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        return int((time.perf_counter() - start) * 1000)
