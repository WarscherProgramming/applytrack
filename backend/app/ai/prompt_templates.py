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
# Prompts live here, never inline in feature services, so they can be reviewed
# and versioned in one place. Feature templates are added as features land.
# ---------------------------------------------------------------------------

_EXAMPLE_TEMPLATE = PromptTemplate(
    name="example.echo",
    description="Placeholder template demonstrating the prompt mechanism.",
    system="You are a helpful assistant. Respond only with JSON.",
    user='Summarise the following text in one sentence as {"summary": "..."}:\n\n{{ text }}',
)

# Resume Match (Milestone 19B). The system prompt pins the output contract; the
# user prompt carries the extracted resume text and the pasted job description.
# Note the {{ var }} delimiters — single braces below would be literal, which is
# why the platform deliberately uses double braces (see prompt_renderer).
_RESUME_MATCH_TEMPLATE = PromptTemplate(
    name="resume_match.v1",
    description="Analyse how well a resume matches a job description.",
    system=(
        "You are an expert technical recruiter and resume coach. You compare a "
        "candidate's resume against a job description and produce an honest, "
        "specific match analysis. Respond with ONLY a single JSON object that "
        "matches the requested schema exactly — no markdown, no code fences, no "
        "commentary. Every list field must be an array of concise strings."
    ),
    user=(
        "Analyse how well the RESUME matches the JOB DESCRIPTION and return a "
        "JSON object with exactly these keys:\n"
        "- overall_match_score: integer from 0 to 100\n"
        "- strengths: array of strings (where the candidate fits well)\n"
        "- weaknesses: array of strings (gaps or weak areas relative to the role)\n"
        "- missing_skills: array of strings (required skills absent from the resume)\n"
        "- recommended_keywords: array of strings (ATS keywords to add)\n"
        "- recommended_resume_changes: array of strings (specific edits to make)\n"
        "- interview_topics: array of strings (topics likely to come up)\n\n"
        "RESUME:\n{{ resume_text }}\n\n"
        "JOB DESCRIPTION:\n{{ job_description }}"
    ),
)

# Cover Letter Generator (Milestone 20). Produces both Markdown and plain-text
# versions in one structured response. The system prompt forbids fabrication —
# the letter may only draw on experience present in the resume.
_COVER_LETTER_TEMPLATE = PromptTemplate(
    name="cover_letter.v1",
    description="Generate a tailored cover letter from a resume and job posting.",
    system=(
        "You are an expert career writer who drafts concise, compelling, "
        "professional cover letters. Strict rules: personalise the letter to the "
        "specific company and role; draw ONLY on experience and skills that "
        "appear in the candidate's resume — never invent employers, titles, "
        "metrics, or skills; align the letter with the job description's "
        "priorities; keep a confident, natural, non-generic tone. Respond with "
        "ONLY a single JSON object with exactly two string keys: 'markdown' (the "
        "cover letter in Markdown) and 'plain_text' (the same letter as plain "
        "text with no Markdown syntax). No code fences, no commentary."
    ),
    user=(
        "Write a cover letter for this candidate.\n\n"
        "COMPANY: {{ company_name }}\n"
        "JOB TITLE: {{ job_title }}\n\n"
        "JOB DESCRIPTION:\n{{ job_description }}\n\n"
        "CANDIDATE RESUME:\n{{ resume_text }}\n\n"
        "OPTIONAL TEMPLATE / STYLE TO FOLLOW (may be 'None'):\n{{ template }}\n\n"
        "OPTIONAL GUIDANCE FROM THE CANDIDATE (may be 'None'):\n{{ user_notes }}"
    ),
)

_TEMPLATES: dict[str, PromptTemplate] = {
    _EXAMPLE_TEMPLATE.name: _EXAMPLE_TEMPLATE,
    _RESUME_MATCH_TEMPLATE.name: _RESUME_MATCH_TEMPLATE,
    _COVER_LETTER_TEMPLATE.name: _COVER_LETTER_TEMPLATE,
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
