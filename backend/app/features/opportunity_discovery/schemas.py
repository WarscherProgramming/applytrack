from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.features.applications.schema import ApplicationResponse
from app.shared.base_schema import AppBaseModel


class JobProviderName(StrEnum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    RSS = "rss"


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class SkillTag(AppBaseModel):
    name: str
    category: str


class NormalizedJobPosting(AppBaseModel):
    id: str
    provider: JobProviderName
    provider_job_id: str | None = None
    company: str
    title: str
    location: str | None = None
    salary: str | None = None
    employment_type: str | None = None
    work_mode: WorkMode = WorkMode.UNKNOWN
    job_url: str
    posted_at: datetime | None = None
    description: str
    skills: list[SkillTag] = Field(default_factory=list)
    industry: str | None = None


class ProviderIssue(AppBaseModel):
    provider: JobProviderName
    source: str
    message: str


class OpportunitySearchRequest(AppBaseModel):
    query: str | None = Field(None, max_length=255)
    providers: list[JobProviderName] = Field(default_factory=list)
    greenhouse_boards: list[str] = Field(default_factory=list)
    lever_companies: list[str] = Field(default_factory=list)
    ashby_boards: list[str] = Field(default_factory=list)
    rss_feeds: list[str] = Field(default_factory=list)
    remote: WorkMode | None = None
    location: str | None = Field(None, max_length=255)
    min_salary: int | None = Field(None, ge=0)
    technologies: list[str] = Field(default_factory=list)
    resume_id: UUID | None = None
    preferred_location: str | None = Field(None, max_length=255)
    preferred_job_type: str | None = Field(None, max_length=255)
    preferred_industry: str | None = Field(None, max_length=255)
    limit: int = Field(25, ge=1, le=100)


class OpportunityScore(AppBaseModel):
    overall_match_percent: int = Field(..., ge=0, le=100)
    resume_match_score: int | None = Field(None, ge=0, le=100)
    skill_overlap_percent: int | None = Field(None, ge=0, le=100)
    historical_response_rate: float | None = None
    location_score: int | None = Field(None, ge=0, le=100)
    job_type_score: int | None = Field(None, ge=0, le=100)
    industry_score: int | None = Field(None, ge=0, le=100)
    reasoning: list[str] = Field(default_factory=list)
    top_missing_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    recommended_resume_id: UUID | None = None
    recommended_resume_name: str | None = None
    suggested_cover_letter_id: UUID | None = None
    suggested_cover_letter_name: str | None = None


class OpportunityAIExplanationResult(AppBaseModel):
    summary: str
    score_explanation: str
    next_steps: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)


class OpportunityAIExplanation(OpportunityAIExplanationResult):
    available: bool
    provider: str | None = None
    model: str | None = None


class ScoredOpportunity(AppBaseModel):
    posting: NormalizedJobPosting
    score: OpportunityScore
    ai_explanation: OpportunityAIExplanation


class OpportunitySearchResponse(AppBaseModel):
    items: list[ScoredOpportunity]
    total: int
    provider_issues: list[ProviderIssue] = Field(default_factory=list)
    top_technologies: list[SkillTagSummary] = Field(default_factory=list)
    top_industries: list[DistributionSummary] = Field(default_factory=list)
    top_locations: list[DistributionSummary] = Field(default_factory=list)


class SkillTagSummary(AppBaseModel):
    name: str
    category: str
    count: int


class DistributionSummary(AppBaseModel):
    name: str
    count: int


class SaveOpportunityRequest(AppBaseModel):
    posting: NormalizedJobPosting
    resume_id: UUID | None = None
    cover_letter_id: UUID | None = None


class SaveOpportunityResponse(AppBaseModel):
    application: ApplicationResponse
    company_created: bool
