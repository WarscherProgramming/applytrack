from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.shared.base_schema import AppBaseModel


class JobIntelligenceFilters(AppBaseModel):
    date_from: date | None = None
    date_to: date | None = None
    industry: str | None = None
    company: str | None = None
    role: str | None = None


class DistributionItem(AppBaseModel):
    name: str
    count: int
    percentage: float | None = None


class TrendPoint(AppBaseModel):
    period: str
    count: int


class SkillSignal(AppBaseModel):
    name: str
    category: str
    frequency: int
    percentage: float | None
    trend_delta: int
    trend: list[TrendPoint] = Field(default_factory=list)
    industry_distribution: list[DistributionItem] = Field(default_factory=list)
    company_distribution: list[DistributionItem] = Field(default_factory=list)
    role_distribution: list[DistributionItem] = Field(default_factory=list)


class CategoryBreakdown(AppBaseModel):
    category: str
    count: int
    skills: list[SkillSignal] = Field(default_factory=list)


class MissingSkill(AppBaseModel):
    name: str
    category: str
    market_frequency: int
    market_percentage: float | None
    resume_match_gap_count: int
    reason: str


class JobDescriptionSource(AppBaseModel):
    id: str
    source: str
    created_at: datetime
    company: str | None = None
    industry: str | None = None
    role: str | None = None
    resume_id: UUID | None = None
    application_id: UUID | None = None


class JobIntelligenceAIResult(AppBaseModel):
    executive_summary: str
    top_learning_priorities: list[str] = Field(default_factory=list)
    emerging_technologies: list[str] = Field(default_factory=list)
    resume_recommendations: list[str] = Field(default_factory=list)
    skill_investment_suggestions: list[str] = Field(default_factory=list)
    career_direction_suggestions: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class JobIntelligenceAI(AppBaseModel):
    available: bool
    provider: str | None = None
    model: str | None = None
    executive_summary: str
    top_learning_priorities: list[str] = Field(default_factory=list)
    emerging_technologies: list[str] = Field(default_factory=list)
    resume_recommendations: list[str] = Field(default_factory=list)
    skill_investment_suggestions: list[str] = Field(default_factory=list)
    career_direction_suggestions: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class JobIntelligenceResponse(AppBaseModel):
    generated_at: datetime
    filters: JobIntelligenceFilters
    job_description_count: int
    source_count: int
    resume_skill_count: int
    sources: list[JobDescriptionSource] = Field(default_factory=list)
    skill_signals: list[SkillSignal] = Field(default_factory=list)
    category_breakdown: list[CategoryBreakdown] = Field(default_factory=list)
    missing_skills: list[MissingSkill] = Field(default_factory=list)
    industry_breakdown: list[DistributionItem] = Field(default_factory=list)
    company_breakdown: list[DistributionItem] = Field(default_factory=list)
    role_breakdown: list[DistributionItem] = Field(default_factory=list)
    ai_interpretation: JobIntelligenceAI

