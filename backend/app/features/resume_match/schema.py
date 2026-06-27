from uuid import UUID

from pydantic import Field

from app.shared.base_schema import AppBaseModel, EntitySchema


class ResumeMatchResult(AppBaseModel):
    """
    The structured analysis the AI must return.

    Used both as the schema passed to AIClient.generate_structured (so the
    platform validates the model's JSON) and as the nested payload in API
    responses. Lists default to empty so a sparse-but-valid model response never
    breaks the contract.
    """

    overall_match_score: int = Field(..., ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommended_keywords: list[str] = Field(default_factory=list)
    recommended_resume_changes: list[str] = Field(default_factory=list)
    interview_topics: list[str] = Field(default_factory=list)


class ResumeMatchCreate(AppBaseModel):
    """Request body for running a new analysis."""

    resume_id: UUID
    job_description: str = Field(..., min_length=20, max_length=20_000)


class ResumeMatchResponse(EntitySchema):
    """Full analysis record, including the complete result (for reopening)."""

    resume_id: UUID | None
    resume_name: str
    job_description: str
    overall_match_score: int
    result: ResumeMatchResult
    provider: str
    model: str


class ResumeMatchListItem(EntitySchema):
    """Lightweight history row — omits the full result and job description body."""

    resume_id: UUID | None
    resume_name: str
    overall_match_score: int
    job_description_preview: str
    provider: str
    model: str


class ResumeMatchListResponse(AppBaseModel):
    items: list[ResumeMatchListItem]
    total: int
    skip: int
    limit: int
