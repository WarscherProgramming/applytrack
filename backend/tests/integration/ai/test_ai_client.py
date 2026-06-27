"""Integration tests for the AIClient against the MockProvider.

Exercises the full platform path — render-free generate, structured parsing,
retry, and usage persistence to the real test database — without any external
API calls.
"""

import pytest
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.errors import AIResponseError, AITransientError
from app.ai.mock_provider import MockProvider
from app.ai.schemas import GenerationRequest
from app.ai.usage_tracker import AIUsageRecord


class _MatchResult(BaseModel):
    score: int
    summary: str


def _client(provider: MockProvider, **kwargs) -> AIClient:
    return AIClient(provider, default_model="mock-model", **kwargs)


def _records(db: Session) -> list[AIUsageRecord]:
    return list(db.scalars(select(AIUsageRecord)))


class TestGenerate:
    def test_returns_ai_result_with_metadata(self, db: Session) -> None:
        client = _client(MockProvider(default_response="hello"))
        result = client.generate(GenerationRequest(prompt="say hi"), db=db)

        assert result.text == "hello"
        assert result.provider == "mock"
        assert result.model == "mock-model"
        assert result.latency_ms >= 0
        assert result.estimated_cost_usd == 0.0  # mock-model is free

    def test_defaults_model_when_request_omits_it(self, db: Session) -> None:
        client = _client(MockProvider())
        result = client.generate(GenerationRequest(prompt="x"), db=db)
        assert result.model == "mock-model"

    def test_works_without_db_session(self) -> None:
        client = _client(MockProvider(default_response="ok"))
        result = client.generate(GenerationRequest(prompt="x"))
        assert result.text == "ok"


class TestUsagePersistence:
    def test_records_successful_usage(self, db: Session) -> None:
        client = _client(MockProvider(default_response="a b c"))
        client.generate(
            GenerationRequest(prompt="one two"), db=db, feature="resume_match"
        )

        records = _records(db)
        assert len(records) == 1
        record = records[0]
        assert record.provider == "mock"
        assert record.feature == "resume_match"
        assert record.success is True
        assert record.total_tokens == record.prompt_tokens + record.completion_tokens

    def test_records_failure_after_retries(self, db: Session) -> None:
        # Always fails transiently; exhausts retries and records a failure row.
        client = _client(MockProvider(fail_times=99), max_retries=1)
        with pytest.raises(AITransientError):
            client.generate(GenerationRequest(prompt="x"), db=db, feature="resume_match")

        records = _records(db)
        assert len(records) == 1
        assert records[0].success is False
        assert records[0].total_tokens == 0

    def test_no_record_without_db(self, db: Session) -> None:
        # Passing no db must not persist anything to the session under test.
        client = _client(MockProvider(default_response="ok"))
        client.generate(GenerationRequest(prompt="x"))
        assert _records(db) == []


class TestRetryIntegration:
    def test_retries_then_succeeds(self, db: Session) -> None:
        provider = MockProvider(fail_times=1, default_response="recovered")
        client = _client(provider, max_retries=2)
        result = client.generate(GenerationRequest(prompt="x"), db=db)
        assert result.text == "recovered"
        assert provider.calls == 2  # one failure + one success
        # Only the successful call is recorded.
        records = _records(db)
        assert len(records) == 1
        assert records[0].success is True


class TestStructured:
    def test_parses_into_schema(self, db: Session) -> None:
        provider = MockProvider(default_response='{"score": 87, "summary": "good fit"}')
        client = _client(provider)
        structured = client.generate_structured(
            GenerationRequest(prompt="match this"),
            _MatchResult,
            db=db,
            feature="resume_match",
        )

        assert structured.data == _MatchResult(score=87, summary="good fit")
        assert structured.result.provider == "mock"
        # Usage was still tracked.
        assert len(_records(db)) == 1

    def test_forces_json_mode(self, db: Session) -> None:
        captured: dict = {}

        def handler(req: GenerationRequest) -> str:
            captured["json_mode"] = req.json_mode
            return '{"score": 1, "summary": "x"}'

        client = _client(MockProvider(handler=handler))
        client.generate_structured(
            GenerationRequest(prompt="x"), _MatchResult, db=db
        )
        assert captured["json_mode"] is True

    def test_invalid_json_raises_response_error(self, db: Session) -> None:
        client = _client(MockProvider(default_response="not json"))
        with pytest.raises(AIResponseError):
            client.generate_structured(
                GenerationRequest(prompt="x"), _MatchResult, db=db
            )
        # The call itself succeeded, so usage is still recorded.
        assert len(_records(db)) == 1
