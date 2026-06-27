from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.shared.base_schema import AppBaseModel


class IntelligenceFilters(AppBaseModel):
    date_from: date | None = None
    date_to: date | None = None
    compare_date_from: date | None = None
    compare_date_to: date | None = None


class RateMetric(AppBaseModel):
    value: float | None = Field(None, ge=0)
    numerator: int
    denominator: int
    label: str


class ApplicationMetrics(AppBaseModel):
    total_applications: int
    active_applications: int
    response_rate: RateMetric
    interview_rate: RateMetric
    offer_rate: RateMetric
    offer_acceptance_rate: RateMetric
    rejection_rate: RateMetric
    ghost_rate: RateMetric
    average_days_until_first_response: float | None
    average_interview_count_per_application: float | None


class SegmentInsight(AppBaseModel):
    name: str
    total_applications: int
    responses: int
    response_rate: float | None
    average_days_until_first_response: float | None = None


class CompanyInsights(AppBaseModel):
    most_responsive_companies: list[SegmentInsight] = Field(default_factory=list)
    most_responsive_industries: list[SegmentInsight] = Field(default_factory=list)
    most_responsive_locations: list[SegmentInsight] = Field(default_factory=list)
    fastest_response_companies: list[SegmentInsight] = Field(default_factory=list)


class DocumentPerformance(AppBaseModel):
    id: UUID
    name: str
    version: int
    submitted_applications: int
    response_rate: float | None
    interview_rate: float | None
    offer_rate: float | None


class DocumentInsights(AppBaseModel):
    items: list[DocumentPerformance] = Field(default_factory=list)
    highest_interview_rate: DocumentPerformance | None = None
    highest_response_rate: DocumentPerformance | None = None
    highest_offer_rate: DocumentPerformance | None = None


class CountInsight(AppBaseModel):
    name: str
    count: int
    percentage: float | None = None


class TrendInsight(AppBaseModel):
    name: str
    current_count: int
    previous_count: int
    delta: int


class SkillIntelligence(AppBaseModel):
    job_description_count: int
    most_requested_skills: list[CountInsight] = Field(default_factory=list)
    missing_skills: list[CountInsight] = Field(default_factory=list)
    trending_technologies: list[TrendInsight] = Field(default_factory=list)
    frequently_requested_certifications: list[CountInsight] = Field(default_factory=list)


class InterviewIntelligence(AppBaseModel):
    most_common_interview_types: list[CountInsight] = Field(default_factory=list)
    average_interviews_before_offer: float | None
    common_technical_topics: list[CountInsight] = Field(default_factory=list)
    common_behavioral_themes: list[CountInsight] = Field(default_factory=list)


class ComparisonMetric(AppBaseModel):
    name: str
    current: float | None
    previous: float | None
    delta: float | None


class PeriodComparison(AppBaseModel):
    metrics: list[ComparisonMetric] = Field(default_factory=list)


class AIRecommendation(AppBaseModel):
    title: str
    detail: str
    evidence: str


class AIRecommendationResult(AppBaseModel):
    executive_summary: str
    recommendations: list[AIRecommendation] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class AIRecommendations(AppBaseModel):
    available: bool
    provider: str | None = None
    model: str | None = None
    executive_summary: str
    recommendations: list[AIRecommendation] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class CareerIntelligenceResponse(AppBaseModel):
    generated_at: datetime
    filters: IntelligenceFilters
    application_metrics: ApplicationMetrics
    company_insights: CompanyInsights
    resume_insights: DocumentInsights
    cover_letter_insights: DocumentInsights
    skill_intelligence: SkillIntelligence
    interview_intelligence: InterviewIntelligence
    ai_recommendations: AIRecommendations
    comparison: PeriodComparison | None = None

