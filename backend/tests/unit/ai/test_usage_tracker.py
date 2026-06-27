from decimal import Decimal
from unittest.mock import MagicMock

from app.ai.schemas import TokenUsage
from app.ai.usage_tracker import AIUsageRecord, UsageTracker, estimate_cost


class TestEstimateCost:
    def test_known_model_cost(self) -> None:
        # gpt-4o-mini: input 0.00015/1k, output 0.0006/1k.
        usage = TokenUsage.of(1000, 1000)
        cost = estimate_cost("gpt-4o-mini", usage)
        assert cost == Decimal("0.000750")

    def test_mock_model_is_free(self) -> None:
        assert estimate_cost("mock-model", TokenUsage.of(100, 100)) == Decimal("0")

    def test_unknown_model_returns_none(self) -> None:
        assert estimate_cost("some-unlisted-model", TokenUsage.of(10, 10)) is None

    def test_zero_tokens_zero_cost(self) -> None:
        assert estimate_cost("gpt-4o", TokenUsage()) == Decimal("0")


class TestUsageTrackerRecord:
    def test_builds_and_persists_record(self) -> None:
        db = MagicMock()
        tracker = UsageTracker()

        entry = tracker.record(
            db,
            provider="mock",
            model="mock-model",
            usage=TokenUsage.of(10, 5),
            latency_ms=42,
            success=True,
            feature="resume_match",
            estimated_cost_usd=Decimal("0.0"),
        )

        # Flushed, not committed (transaction owned by get_db).
        db.add.assert_called_once()
        db.flush.assert_called_once()

        assert isinstance(entry, AIUsageRecord)
        assert entry.provider == "mock"
        assert entry.feature == "resume_match"
        assert entry.prompt_tokens == 10
        assert entry.completion_tokens == 5
        assert entry.total_tokens == 15
        assert entry.latency_ms == 42
        assert entry.success is True

    def test_records_failure(self) -> None:
        db = MagicMock()
        entry = UsageTracker().record(
            db,
            provider="openai",
            model="gpt-4o-mini",
            usage=TokenUsage(),
            latency_ms=5,
            success=False,
        )
        assert entry.success is False
        assert entry.total_tokens == 0
        assert entry.estimated_cost_usd is None
