from dataclasses import dataclass, field

from app.ai.errors import PromptRenderError
from app.ai.prompt_renderer import extract_variables, render


@dataclass(frozen=True)
class PromptTemplate:
    """
    A named, versioned prompt stored centrally.

    Prompts live here — never inline in feature services — so they can be
    reviewed, versioned, and reused across features. `system` and `user` are
    {{ variable }} templates (see prompt_renderer). `required_variables` is
    derived from both templates at construction time.
    """

    name: str
    user: str
    system: str | None = None
    description: str = ""
    version: int = 1
    required_variables: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        derived = extract_variables(self.user)
        if self.system:
            derived |= extract_variables(self.system)
        # frozen dataclass: use object.__setattr__ to populate the derived field.
        object.__setattr__(self, "required_variables", frozenset(derived))


@dataclass(frozen=True)
class RenderedPrompt:
    """The concrete system/user strings produced by rendering a template."""

    system: str | None
    user: str


# ---------------------------------------------------------------------------
# Central registry.
#
# Feature-specific prompts (Resume Match, Cover Letter AI, Interview Prep) will
# be added here in later milestones. For now it holds one example template that
# documents the structure and gives the platform something concrete to exercise.
# ---------------------------------------------------------------------------

_EXAMPLE_TEMPLATE = PromptTemplate(
    name="example.echo",
    description="Placeholder template demonstrating the prompt mechanism.",
    system="You are a helpful assistant. Respond only with JSON.",
    user='Summarise the following text in one sentence as {"summary": "..."}:\n\n{{ text }}',
)

_TEMPLATES: dict[str, PromptTemplate] = {
    _EXAMPLE_TEMPLATE.name: _EXAMPLE_TEMPLATE,
}


def register_template(template: PromptTemplate) -> None:
    """Register a template (used by features and by tests)."""
    _TEMPLATES[template.name] = template


def get_template(name: str) -> PromptTemplate:
    template = _TEMPLATES.get(name)
    if template is None:
        raise PromptRenderError(f"Unknown prompt template: {name!r}")
    return template


def render_template(name: str, variables: dict[str, object]) -> RenderedPrompt:
    """Look up a named template and render its system/user parts."""
    template = get_template(name)
    system = render(template.system, variables) if template.system else None
    user = render(template.user, variables)
    return RenderedPrompt(system=system, user=user)
