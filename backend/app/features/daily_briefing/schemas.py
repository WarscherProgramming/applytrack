from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.features.daily_briefing.model import NotificationCategory, NotificationPriority
from app.shared.base_schema import AppBaseModel, EntitySchema


class BriefingItem(AppBaseModel):
    id: str
    title: str
    detail: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    category: NotificationCategory | None = None
    due_at: datetime | None = None
    action_url: str | None = None


class RecruiterEmailItem(AppBaseModel):
    id: UUID
    subject: str
    sender: str
    sent_at: datetime
    match_reason: str | None = None


class OpportunityHighlight(AppBaseModel):
    id: UUID
    company: str
    title: str
    created_at: datetime
    source: str | None = None
    job_url: str | None = None


class ResumePerformanceChange(AppBaseModel):
    title: str
    detail: str
    evidence: str | None = None


class SkillTrendUpdate(AppBaseModel):
    skill: str
    category: str
    frequency: int
    trend_delta: int
    percentage: float | None = None


class DailyBriefingAIResult(AppBaseModel):
    morning_summary: str
    recommendations: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class DailyBriefingAI(DailyBriefingAIResult):
    available: bool
    provider: str | None = None
    model: str | None = None


class NotificationResponse(EntitySchema):
    title: str
    message: str
    category: NotificationCategory
    priority: NotificationPriority
    source_type: str | None
    source_id: str | None
    action_url: str | None
    dedupe_key: str
    is_read: bool
    is_pinned: bool
    is_dismissed: bool


class NotificationListResponse(AppBaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    pinned_count: int


class NotificationUpdate(AppBaseModel):
    is_read: bool | None = None
    is_pinned: bool | None = None
    is_dismissed: bool | None = None


class DailyBriefingResponse(AppBaseModel):
    generated_at: datetime
    briefing_date: date
    morning_summary: str
    followups_due_today: list[BriefingItem] = Field(default_factory=list)
    overdue_followups: list[BriefingItem] = Field(default_factory=list)
    upcoming_interviews: list[BriefingItem] = Field(default_factory=list)
    new_recruiter_emails: list[RecruiterEmailItem] = Field(default_factory=list)
    newly_discovered_opportunities: list[OpportunityHighlight] = Field(default_factory=list)
    resume_performance_changes: list[ResumePerformanceChange] = Field(default_factory=list)
    skill_trend_updates: list[SkillTrendUpdate] = Field(default_factory=list)
    ai_recommendations: list[str] = Field(default_factory=list)
    prioritized_actions: list[BriefingItem] = Field(default_factory=list)
    pinned_notifications: list[NotificationResponse] = Field(default_factory=list)
    unread_notification_count: int
    ai_narrative: DailyBriefingAI
