from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.shared.base_schema import AppBaseModel


class PipelineStage(AppBaseModel):
    status: str
    count: int


class TodayMetrics(AppBaseModel):
    active_applications: int
    followups_due_today: int
    overdue_followups: int
    upcoming_interviews: int
    recent_emails: int
    response_rate: float | None
    interview_rate: float | None


class PriorityItem(AppBaseModel):
    id: str
    rank: int
    title: str
    detail: str
    reason: str
    priority: str = Field(pattern="^(urgent|high|medium|low)$")
    source: str
    due_at: datetime | None = None


class DeadlineItem(AppBaseModel):
    id: str
    kind: str
    title: str
    subtitle: str | None = None
    due_at: datetime
    priority: str = Field(pattern="^(urgent|high|medium|low)$")


class TimelineItem(AppBaseModel):
    id: str
    kind: str
    title: str
    subtitle: str | None = None
    timestamp: datetime


class GmailActivityItem(AppBaseModel):
    id: UUID
    subject: str
    sender: str
    sent_at: datetime
    direction: str
    match_reason: str | None = None


class UpcomingInterviewItem(AppBaseModel):
    id: UUID
    application_id: UUID
    title: str
    interview_type: str | None
    scheduled_at: datetime
    location: str | None = None


class SkillFocus(AppBaseModel):
    skill: str
    count: int
    percentage: float | None = None
    reason: str


class ResumeRecommendation(AppBaseModel):
    title: str
    detail: str
    evidence: str | None = None


class Reminder(AppBaseModel):
    title: str
    detail: str
    due_date: date | None = None
    severity: str = Field(pattern="^(urgent|high|medium|low)$")


class CopilotBriefingResult(AppBaseModel):
    executive_summary: str
    ai_recommendations: list[str] = Field(default_factory=list)
    skill_focus: str
    resume_recommendation: str
    interview_preparation_reminder: str
    follow_up_reminder: str
    caveats: list[str] = Field(default_factory=list)


class CopilotNarrative(AppBaseModel):
    available: bool
    provider: str | None = None
    model: str | None = None
    executive_summary: str
    ai_recommendations: list[str] = Field(default_factory=list)
    skill_focus: str
    resume_recommendation: str
    interview_preparation_reminder: str
    follow_up_reminder: str
    caveats: list[str] = Field(default_factory=list)


class DailyBriefing(AppBaseModel):
    generated_at: datetime
    executive_summary: str
    top_priorities: list[PriorityItem] = Field(default_factory=list)
    upcoming_deadlines: list[DeadlineItem] = Field(default_factory=list)
    ai_recommendations: list[str] = Field(default_factory=list)
    skill_focus: list[SkillFocus] = Field(default_factory=list)
    resume_recommendation: ResumeRecommendation | None = None
    interview_preparation_reminder: Reminder
    follow_up_reminder: Reminder


class CareerCopilotResponse(AppBaseModel):
    generated_at: datetime
    briefing: DailyBriefing
    today_metrics: TodayMetrics
    application_pipeline: list[PipelineStage] = Field(default_factory=list)
    upcoming_timeline: list[TimelineItem] = Field(default_factory=list)
    recent_gmail_activity: list[GmailActivityItem] = Field(default_factory=list)
    upcoming_interviews: list[UpcomingInterviewItem] = Field(default_factory=list)
    deterministic_priorities: list[PriorityItem] = Field(default_factory=list)
    ai_insight_panel: CopilotNarrative

