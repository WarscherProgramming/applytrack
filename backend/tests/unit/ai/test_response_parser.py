import pytest
from pydantic import BaseModel

from app.ai.errors import AIResponseError
from app.ai.response_parser import parse_json, parse_model


class _Sample(BaseModel):
    score: int
    label: str


class TestParseJson:
    def test_parses_plain_json(self) -> None:
        assert parse_json('{"a": 1}') == {"a": 1}

    def test_strips_json_code_fence(self) -> None:
        text = '```json\n{"a": 1}\n```'
        assert parse_json(text) == {"a": 1}

    def test_strips_bare_code_fence(self) -> None:
        text = '```\n{"a": 1}\n```'
        assert parse_json(text) == {"a": 1}

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(AIResponseError, match="valid JSON"):
            parse_json("not json at all")


class TestParseModel:
    def test_parses_and_validates(self) -> None:
        result = parse_model('{"score": 9, "label": "great"}', _Sample)
        assert result == _Sample(score=9, label="great")

    def test_parses_model_inside_fence(self) -> None:
        result = parse_model('```json\n{"score": 1, "label": "x"}\n```', _Sample)
        assert result.score == 1

    def test_raises_on_schema_mismatch(self) -> None:
        # Missing required "label" field.
        with pytest.raises(AIResponseError, match="_Sample"):
            parse_model('{"score": 9}', _Sample)

    def test_raises_on_wrong_type(self) -> None:
        with pytest.raises(AIResponseError):
            parse_model('{"score": "not-an-int", "label": "x"}', _Sample)

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(AIResponseError, match="valid JSON"):
            parse_model("garbage", _Sample)
