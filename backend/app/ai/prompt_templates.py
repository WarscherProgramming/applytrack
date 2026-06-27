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

# Interview Preparation (Milestone 21). Produces a full prep package as one
# structured JSON object. The system prompt forbids fabricating experience and
# forbids inventing company news (the platform has no web access), instructing a
# clear stored-data-only disclaimer instead.
_INTERVIEW_PREP_TEMPLATE = PromptTemplate(
    name="interview_prep.v1",
    description="Generate a complete interview-preparation package.",
    system=(
        "You are an expert interview coach. You prepare candidates for specific "
        "interviews using only the information provided. Strict rules: NEVER "
        "fabricate the candidate's experience — STAR examples must be grounded in "
        "their resume; if the resume is missing or thin, return STAR examples as "
        "clearly-labelled reusable templates instead of invented stories. You "
        "have NO access to the internet: do not invent recent company news — if "
        "you lack verified recent news, set recent_news to a short note that the "
        "overview is based only on provided/stored data. Respond with ONLY a "
        "single JSON object matching the requested schema exactly — no markdown, "
        "no code fences, no commentary. Every list field is an array of strings "
        "unless stated otherwise."
    ),
    user=(
        "Prepare the candidate for this interview. Return a JSON object with "
        "exactly these keys:\n"
        "- company_overview: object { mission: string, products_services: "
        "string[], industry: string, culture: string, recent_news: string }\n"
        "- likely_questions: object { behavioral: string[], technical: string[], "
        "role_specific: string[], company_specific: string[] }\n"
        "- star_examples: array of objects { question, situation, task, action, "
        "result } (all strings)\n"
        "- study_topics: object { languages: string[], frameworks: string[], "
        "concepts: string[], system_design: string[], algorithms: string[], "
        "role_specific: string[] }\n"
        "- questions_to_ask: string[]\n"
        "- red_flags: object { missing_resume_coverage: string[], skill_gaps: "
        "string[], likely_challenges: string[] }\n"
        "- checklist: string[] (research, portfolio, resume review, questions, "
        "logistics)\n\n"
        "COMPANY: {{ company_name }}\n"
        "JOB TITLE: {{ job_title }}\n"
        "INTERVIEW TYPE: {{ interview_type }}\n"
        "INTERVIEW ROUND: {{ interview_round }}\n\n"
        "JOB DESCRIPTION:\n{{ job_description }}\n\n"
        "CANDIDATE RESUME:\n{{ resume_text }}\n\n"
        "ADDITIONAL CONTEXT (recruiter/interview notes, recent emails; may be "
        "'None'):\n{{ additional_context }}"
    ),
)

_CAREER_INTELLIGENCE_TEMPLATE = PromptTemplate(
    name="career_intelligence.v1",
    description="Interpret computed career analytics into concise recommendations.",
    system=(
        "You are a career intelligence analyst. You receive computed analytics "
        "from a job-search CRM and turn them into concise, actionable "
        "recommendations. Strict rules: use ONLY the supplied analytics JSON; "
        "do not invent statistics, companies, industries, skills, or trends; if "
        "a metric is null or has a tiny denominator, state the limitation. "
        "Respond with ONLY a single JSON object with keys: executive_summary "
        "(string), recommendations (array of objects with title, detail, "
        "evidence strings), and caveats (array of strings)."
    ),
    user=(
        "Interpret this ApplyTrack career analytics payload and produce up to "
        "six recommendations. Be direct and evidence-based.\n\n"
        "ANALYTICS JSON:\n{{ analytics_json }}"
    ),
)

_CAREER_COPILOT_TEMPLATE = PromptTemplate(
    name="career_copilot.v1",
    description="Turn deterministic career briefing facts into a daily copilot narrative.",
    system=(
        "You are ApplyTrack's career copilot. You receive a deterministic daily "
        "briefing JSON generated from the user's tracked applications, Gmail, "
        "follow-ups, interviews, and career intelligence metrics. Use ONLY the "
        "provided facts. Do not invent statistics, deadlines, companies, or "
        "skills. If data is sparse, say so plainly. Respond with ONLY one JSON "
        "object with keys: executive_summary (string), ai_recommendations "
        "(array of strings), skill_focus (string), resume_recommendation "
        "(string), interview_preparation_reminder (string), follow_up_reminder "
        "(string), and caveats (array of strings)."
    ),
    user=(
        "Write today's career copilot briefing from this computed data. Keep it "
        "concise, prioritized, and actionable.\n\n"
        "BRIEFING JSON:\n{{ briefing_json }}"
    ),
)

_JOB_INTELLIGENCE_TEMPLATE = PromptTemplate(
    name="job_intelligence.v1",
    description="Interpret deterministic job-market skill intelligence.",
    system=(
        "You are a job-market intelligence analyst for a job seeker. You receive "
        "deterministic analytics extracted from saved job descriptions and resume "
        "data. Use ONLY the supplied JSON. Do not invent statistics, market "
        "trends, companies, skills, or resume facts. If sample size is small or "
        "a field is empty, state that clearly. Respond with ONLY one JSON object "
        "with keys: executive_summary (string), top_learning_priorities (array "
        "of strings), emerging_technologies (array of strings), "
        "resume_recommendations (array of strings), skill_investment_suggestions "
        "(array of strings), career_direction_suggestions (array of strings), "
        "and caveats (array of strings)."
    ),
    user=(
        "Interpret this ApplyTrack Job Intelligence payload. Keep recommendations "
        "specific, concise, and grounded in the computed evidence.\n\n"
        "JOB INTELLIGENCE JSON:\n{{ job_intelligence_json }}"
    ),
)

_OPPORTUNITY_DISCOVERY_TEMPLATE = PromptTemplate(
    name="opportunity_discovery.v1",
    description="Explain deterministic opportunity discovery scores.",
    system=(
        "You are ApplyTrack's opportunity discovery analyst. You receive one "
        "normalized job posting and a deterministic score computed from resume "
        "skills, missing skills, preferences, and historical ApplyTrack data. "
        "Use ONLY the supplied JSON. Do not invent salary, company facts, "
        "statistics, or application outcomes. If data is sparse, say so plainly. "
        "Respond with ONLY one JSON object with keys: summary (string), "
        "score_explanation (string), next_steps (array of strings), and "
        "cautions (array of strings)."
    ),
    user=(
        "Explain this opportunity score concisely and actionably.\n\n"
        "OPPORTUNITY SCORE JSON:\n{{ opportunity_score_json }}"
    ),
)

_TEMPLATES: dict[str, PromptTemplate] = {
    _EXAMPLE_TEMPLATE.name: _EXAMPLE_TEMPLATE,
    _RESUME_MATCH_TEMPLATE.name: _RESUME_MATCH_TEMPLATE,
    _COVER_LETTER_TEMPLATE.name: _COVER_LETTER_TEMPLATE,
    _INTERVIEW_PREP_TEMPLATE.name: _INTERVIEW_PREP_TEMPLATE,
    _CAREER_INTELLIGENCE_TEMPLATE.name: _CAREER_INTELLIGENCE_TEMPLATE,
    _CAREER_COPILOT_TEMPLATE.name: _CAREER_COPILOT_TEMPLATE,
    _JOB_INTELLIGENCE_TEMPLATE.name: _JOB_INTELLIGENCE_TEMPLATE,
    _OPPORTUNITY_DISCOVERY_TEMPLATE.name: _OPPORTUNITY_DISCOVERY_TEMPLATE,
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
