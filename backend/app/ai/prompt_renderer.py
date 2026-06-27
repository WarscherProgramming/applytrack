import re
from typing import Any

from app.ai.errors import PromptRenderError

# Variables use a mustache-style {{ name }} delimiter rather than str.format's
# single braces. This is deliberate: prompts frequently contain literal JSON
# examples full of { and }, which would break str.format/% interpolation. Double
# braces let those literals pass through untouched while still supporting
# validated variable substitution.
_VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


def extract_variables(template: str) -> set[str]:
    """Return the set of variable names referenced in a template."""
    return set(_VARIABLE_PATTERN.findall(template))


def render(template: str, variables: dict[str, Any]) -> str:
    """
    Substitute {{ name }} placeholders with values from `variables`.

    Raises PromptRenderError if any referenced variable is missing — surfacing
    the mistake immediately rather than sending a half-formed prompt to a
    provider. Extra, unused variables are ignored.
    """
    required = extract_variables(template)
    missing = sorted(required - variables.keys())
    if missing:
        raise PromptRenderError(
            f"Missing prompt variable(s): {', '.join(missing)}"
        )

    def _replace(match: re.Match[str]) -> str:
        return str(variables[match.group(1)])

    return _VARIABLE_PATTERN.sub(_replace, template)
