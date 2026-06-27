from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.shared.base_schema import AppBaseModel


class CoverLetterGenerateRequest(AppBaseModel):
    """Inputs for generating a cover letter.

    `resume_id` and `job_description` are required. company/job title may be
    supplied directly or derived from a selected application; the service
    resolves and validates the final values.
    """

    resume_id: UUID
    job_description: str = Field(..., min_length=20, max_length=20_000)
    application_id: UUID | None = None
    company_name: str | None = Field(None, max_length=255)
    job_title: str | None = Field(None, max_length=255)
    template_cover_letter_id: UUID | None = None
    user_notes: str | None = Field(None, max_length=5_000)


class CoverLetterGeneration(AppBaseModel):
    """The structured output the AI must return (both letter formats)."""

    markdown: str = Field(..., min_length=1)
    plain_text: str = Field(..., min_length=1)


class UsageSummary(AppBaseModel):
    """Token/cost/latency summary surfaced to the UI."""

    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float | None = None
    latency_ms: int


class CoverLetterGenerateResponse(AppBaseModel):
    """A generated (not-yet-saved) cover letter plus context and usage."""

    markdown: str
    plain_text: str
    # Resolved context (echoed so the UI can label / name the saved version).
    resume_name: str
    company_name: str
    job_title: str
    usage: UsageSummary


class CoverLetterSaveRequest(AppBaseModel):
    """Persist a (possibly edited) letter as a new version in the library."""

    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=50_000)
    notes: str | None = Field(None, max_length=5_000)


class CoverLetterVersionContent(AppBaseModel):
    """A single stored cover-letter version, with its text, for comparison."""

    id: UUID
    name: str
    version: int
    file_name: str
    created_at: datetime
    content: str


class CoverLetterVersionsResponse(AppBaseModel):
    items: list[CoverLetterVersionContent]
