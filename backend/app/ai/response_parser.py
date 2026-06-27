import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.ai.errors import AIResponseError

# Models sometimes wrap JSON in a ```json ... ``` markdown fence even when asked
# not to; strip a single leading/trailing fence before parsing.
_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)

T = TypeVar("T", bound=BaseModel)


def _strip_code_fences(text: str) -> str:
    return _FENCE.sub("", text.strip())


def parse_json(text: str) -> Any:
    """
    Parse a provider's text response as JSON.

    Raises AIResponseError (non-retryable) with a clear message on malformed
    JSON — retrying the same request would not fix bad output.
    """
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIResponseError(
            f"Provider did not return valid JSON: {exc}"
        ) from exc


def parse_model(text: str, model: type[T]) -> T:
    """
    Parse JSON text and validate it against a Pydantic model.

    Raises AIResponseError if the JSON is invalid or does not match the schema,
    so callers always get either a fully-validated model or a clear failure.
    """
    data = parse_json(text)
    try:
        return model.model_validate(data)
    except PydanticValidationError as exc:
        raise AIResponseError(
            f"Response did not match {model.__name__}: {exc}"
        ) from exc
