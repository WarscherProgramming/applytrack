import logging
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.ai.schemas import TokenUsage
from app.shared.base_model import BaseModel

logger = logging.getLogger(__name__)


class AIUsageRecord(BaseModel):
    """
    One row per AI generation, successful or failed.

    Persisted so cost, token consumption, and latency can be monitored and, in
    later milestones, attributed per feature and surfaced in Analytics.
    """

    __tablename__ = "ai_usage_records"

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # The feature that made the call (e.g. "resume_match"). Nullable: the
    # platform itself may make calls not tied to a feature.
    feature: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Estimated, not billed — Numeric avoids float rounding drift on money.
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 6), nullable=True
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# USD per 1,000 tokens, as (input, output). Estimates for monitoring only — the
# table is the source of truth, so stale prices never corrupt billing. Unknown
# models yield a None cost (logged) rather than a wrong number.
_PRICING_PER_1K: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4o": (Decimal("0.0025"), Decimal("0.01")),
    "gpt-4o-mini": (Decimal("0.00015"), Decimal("0.0006")),
    "mock-model": (Decimal("0"), Decimal("0")),
}


def estimate_cost(model: str, usage: TokenUsage) -> Decimal | None:
    """Estimate the USD cost of a generation, or None for an unpriced model."""
    pricing = _PRICING_PER_1K.get(model)
    if pricing is None:
        logger.debug("No pricing for model %r; cost left unestimated", model)
        return None
    input_rate, output_rate = pricing
    cost = (
        Decimal(usage.prompt_tokens) / 1000 * input_rate
        + Decimal(usage.completion_tokens) / 1000 * output_rate
    )
    return cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


class UsageTracker:
    """Builds and persists AIUsageRecord rows.

    Persistence uses flush() only — never commit() — so it respects the request
    transaction owned by get_db(), exactly like the repositories.
    """

    def record(
        self,
        db: Session,
        *,
        provider: str,
        model: str,
        usage: TokenUsage,
        latency_ms: int,
        success: bool,
        feature: str | None = None,
        user_id: UUID | None = None,
        estimated_cost_usd: Decimal | None = None,
    ) -> AIUsageRecord:
        entry = AIUsageRecord(
            user_id=user_id,
            provider=provider,
            model=model,
            feature=feature,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            latency_ms=latency_ms,
            success=success,
        )
        db.add(entry)
        db.flush()
        logger.info(
            "AI usage provider=%s model=%s feature=%s tokens=%d cost=%s latency=%dms ok=%s",
            provider,
            model,
            feature,
            usage.total_tokens,
            estimated_cost_usd,
            latency_ms,
            success,
        )
        return entry
