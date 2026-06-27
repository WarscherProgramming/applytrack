from uuid import UUID

from pydantic import Field

from app.shared.base_schema import AppBaseModel, EntitySchema


# ---------------------------------------------------------------------------
# Structured AI output. These nested models are what the AI must return and are
# validated by the platform's response parser, so a malformed package is
# rejected before it is ever stored.
# ---------------------------------------------------------------------------


class CompanyOverview(AppBaseModel):
    mission: str = ""
    products_services: list[str] = Field(default_factory=list)
    industry: str = ""
    culture: str = ""
    # May be a disclaimer that only stored/provided data was used (no web access).
    recent_news: str = ""


class LikelyQuestions(AppBaseModel):
    behavioral: list[str] = Field(default_factory=list)
    technical: list[str] = Field(default_factory=list)
    role_specific: list[str] = Field(default_factory=list)
    company_specific: list[str] = Field(default_factory=list)


class StarExample(AppBaseModel):
    question: str = ""
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""


class StudyTopics(AppBaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    system_design: list[str] = Field(default_factory=list)
    algorithms: list[str] = Field(default_factory=list)
    role_specific: list[str] = Field(default_factory=list)


class RedFlags(AppBaseModel):
    missing_resume_coverage: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    likely_challenges: list[str] = Field(default_factory=list)


class InterviewPrepResult(AppBaseModel):
    """The complete preparation package returned by the AI and stored as JSONB."""

    company_overview: CompanyOverview
    likely_questions: LikelyQuestions
    star_examples: list[StarExample] = Field(default_factory=list)
    study_topics: StudyTopics
    questions_to_ask: list[str] = Field(default_factory=list)
    red_flags: RedFlags
    checklist: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API request / response models.
# ---------------------------------------------------------------------------


class InterviewPrepRequest(AppBaseModel):
    application_id: UUID | None = None
    resume_id: UUID | None = None
    company_name: str | None = Field(None, max_length=255)
    job_title: str | None = Field(None, max_length=255)
    job_description: str = Field(..., min_length=20, max_length=20_000)
    interview_type: str | None = Field(None, max_length=100)
    interview_round: str | None = Field(None, max_length=100)
    recruiter_notes: str | None = Field(None, max_length=5_000)
    interview_notes: str | None = Field(None, max_length=5_000)


class UsageSummary(AppBaseModel):
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float | None = None
    latency_ms: int


class InterviewPrepResponse(EntitySchema):
    application_id: UUID | None
    resume_id: UUID | None
    company_name: str
    job_title: str
    interview_type: str | None
    interview_round: str | None
    job_description: str
    result: InterviewPrepResult
    usage: UsageSummary


class InterviewPrepListItem(EntitySchema):
    application_id: UUID | None
    company_name: str
    job_title: str
    interview_type: str | None
    interview_round: str | None
    provider: str
    model: str


class InterviewPrepListResponse(AppBaseModel):
    items: list[InterviewPrepListItem]
    total: int
    skip: int
    limit: int
