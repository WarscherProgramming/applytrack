import hashlib
import json
import logging
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.ai.errors import AIError
from app.core.config import settings
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.career_copilot.repository import CareerCopilotRepository
from app.features.career_copilot.schemas import (
    CareerCopilotResponse,
    CopilotBriefingResult,
    CopilotNarrative,
    DailyBriefing,
    DeadlineItem,
    GmailActivityItem,
    PipelineStage,
    PriorityItem,
    Reminder,
    ResumeRecommendation,
    SkillFocus,
    TimelineItem,
    TodayMetrics,
    UpcomingInterviewItem,
)
from app.features.career_intelligence.schemas import CareerIntelligenceResponse
from app.features.career_intelligence.service import CareerIntelligenceService
from app.features.followups.model import FollowUp, FollowUpStatus
from app.features.gmail.models import EmailMessage
from app.features.interviews.model import Interview

logger = logging.getLogger(__name__)

FEATURE = "career_copilot"
PROMPT_TEMPLATE = "career_copilot.v1"
TERMINAL_STATUSES = {
    ApplicationStatus.ACCEPTED.value,
    ApplicationStatus.REJECTED.value,
    ApplicationStatus.WITHDRAWN.value,
    ApplicationStatus.GHOSTED.value,
}
PRIORITY_WEIGHTS = {"urgent": 4, "high": 3, "medium": 2, "low": 1}


class CareerCopilotService:
    """
    Orchestrates the daily career briefing.

    This service deliberately reuses Career Intelligence for analytics. It only
    adds time-sensitive aggregation and priority ranking, then uses the existing
    AI platform to narrate those computed facts.
    """

    def __init__(self, db: Session, user_id: UUID, *, ai_client: AIClient | None = None) -> None:
        self.db = db
        self.user_id = user_id
        self.repo = CareerCopilotRepository(db, user_id)
        self._injected_client = ai_client

    def build_daily_briefing(self) -> CareerCopilotResponse:
        now = datetime.now(UTC)
        today = now.date()

        intelligence = CareerIntelligenceService(self.db, self.user_id).build_dashboard()
        applications = self.repo.list_applications()
        companies = self.repo.list_companies()
        followups = self.repo.list_followups()
        upcoming_interviews = self.repo.list_upcoming_interviews(now=now)
        recent_emails = self.repo.list_recent_emails(since=now - timedelta(days=7))

        company_by_id = {company.id: company for company in companies}
        app_by_id = {app.id: app for app in applications}

        metrics = self._today_metrics(
            intelligence=intelligence,
            applications=applications,
            followups=followups,
            interviews=upcoming_interviews,
            emails=recent_emails,
            today=today,
        )
        pipeline = self._pipeline(applications)
        gmail_activity = self._gmail_activity(recent_emails)
        interview_items = self._upcoming_interviews(upcoming_interviews, app_by_id)
        deadlines = self._deadlines(followups, upcoming_interviews, app_by_id, today)
        deterministic_priorities = self._priorities(
            intelligence=intelligence,
            followups=followups,
            interviews=upcoming_interviews,
            applications=applications,
            companies=company_by_id,
            today=today,
        )
        timeline = self._timeline(deadlines, gmail_activity)
        skill_focus = self._skill_focus(intelligence)
        resume_recommendation = self._resume_recommendation(intelligence)
        interview_reminder = self._interview_reminder(upcoming_interviews, app_by_id, today)
        followup_reminder = self._followup_reminder(followups, today)

        facts = {
            "today": today.isoformat(),
            "today_metrics": metrics.model_dump(mode="json"),
            "application_pipeline": [item.model_dump(mode="json") for item in pipeline],
            "top_priorities": [
                item.model_dump(mode="json") for item in deterministic_priorities[:6]
            ],
            "upcoming_deadlines": [item.model_dump(mode="json") for item in deadlines[:8]],
            "recent_gmail_activity": [
                item.model_dump(mode="json") for item in gmail_activity[:5]
            ],
            "upcoming_interviews": [
                item.model_dump(mode="json") for item in interview_items[:5]
            ],
            "skill_focus": [item.model_dump(mode="json") for item in skill_focus[:5]],
            "resume_recommendation": (
                resume_recommendation.model_dump(mode="json")
                if resume_recommendation
                else None
            ),
            "career_intelligence_summary": {
                "executive_summary": intelligence.ai_recommendations.executive_summary,
                "recommendations": [
                    item.model_dump(mode="json")
                    for item in intelligence.ai_recommendations.recommendations
                ],
                "caveats": intelligence.ai_recommendations.caveats,
            },
        }
        narrative = self._narrative(facts)
        generated_at = datetime.now(UTC)

        briefing = DailyBriefing(
            generated_at=generated_at,
            executive_summary=narrative.executive_summary,
            top_priorities=deterministic_priorities[:6],
            upcoming_deadlines=deadlines[:8],
            ai_recommendations=narrative.ai_recommendations,
            skill_focus=skill_focus[:5],
            resume_recommendation=resume_recommendation,
            interview_preparation_reminder=Reminder(
                title="Interview preparation",
                detail=narrative.interview_preparation_reminder,
                due_date=interview_reminder.due_date,
                severity=interview_reminder.severity,
            ),
            follow_up_reminder=Reminder(
                title="Follow-up reminder",
                detail=narrative.follow_up_reminder,
                due_date=followup_reminder.due_date,
                severity=followup_reminder.severity,
            ),
        )
        return CareerCopilotResponse(
            generated_at=generated_at,
            briefing=briefing,
            today_metrics=metrics,
            application_pipeline=pipeline,
            upcoming_timeline=timeline[:12],
            recent_gmail_activity=gmail_activity,
            upcoming_interviews=interview_items,
            deterministic_priorities=deterministic_priorities,
            ai_insight_panel=narrative,
        )

    def _today_metrics(
        self,
        *,
        intelligence: CareerIntelligenceResponse,
        applications: list[JobApplication],
        followups: list[FollowUp],
        interviews: list[Interview],
        emails: list[EmailMessage],
        today: date,
    ) -> TodayMetrics:
        pending = [
            item for item in followups if item.status == FollowUpStatus.PENDING.value
        ]
        return TodayMetrics(
            active_applications=sum(
                1 for app in applications if app.status not in TERMINAL_STATUSES
            ),
            followups_due_today=sum(1 for item in pending if item.due_date == today),
            overdue_followups=sum(1 for item in pending if item.due_date < today),
            upcoming_interviews=sum(
                1 for item in interviews if item.scheduled_at.date() <= today + timedelta(days=7)
            ),
            recent_emails=len(emails),
            response_rate=intelligence.application_metrics.response_rate.value,
            interview_rate=intelligence.application_metrics.interview_rate.value,
        )

    @staticmethod
    def _pipeline(applications: list[JobApplication]) -> list[PipelineStage]:
        counts = Counter(app.status for app in applications)
        order = [status.value for status in ApplicationStatus]
        return [
            PipelineStage(status=status, count=counts[status])
            for status in order
            if counts[status]
        ]

    @staticmethod
    def _gmail_activity(emails: list[EmailMessage]) -> list[GmailActivityItem]:
        return [
            GmailActivityItem(
                id=email.id,
                subject=email.subject or "(no subject)",
                sender=email.sender,
                sent_at=email.sent_at,
                direction=email.direction,
                match_reason=email.match_reason,
            )
            for email in emails
        ]

    @staticmethod
    def _upcoming_interviews(
        interviews: list[Interview], app_by_id: dict
    ) -> list[UpcomingInterviewItem]:
        items = []
        for interview in interviews:
            app = app_by_id.get(interview.application_id)
            items.append(
                UpcomingInterviewItem(
                    id=interview.id,
                    application_id=interview.application_id,
                    title=app.job_title if app else "Interview",
                    interview_type=interview.interview_type,
                    scheduled_at=interview.scheduled_at,
                    location=interview.location or interview.meeting_link,
                )
            )
        return items

    def _deadlines(
        self,
        followups: list[FollowUp],
        interviews: list[Interview],
        app_by_id: dict,
        today: date,
    ) -> list[DeadlineItem]:
        rows: list[DeadlineItem] = []
        for followup in followups:
            if followup.status != FollowUpStatus.PENDING.value:
                continue
            due_at = datetime.combine(followup.due_date, time(hour=9), tzinfo=UTC)
            rows.append(
                DeadlineItem(
                    id=f"followup-{followup.id}",
                    kind="followup",
                    title=followup.title,
                    subtitle=followup.followup_type.replace("_", " "),
                    due_at=due_at,
                    priority=self._deadline_priority(followup.due_date, today),
                )
            )
        for interview in interviews:
            app = app_by_id.get(interview.application_id)
            rows.append(
                DeadlineItem(
                    id=f"interview-{interview.id}",
                    kind="interview",
                    title=app.job_title if app else "Interview",
                    subtitle=interview.interview_type,
                    due_at=interview.scheduled_at,
                    priority=self._deadline_priority(interview.scheduled_at.date(), today),
                )
            )
        rows.sort(key=lambda item: (PRIORITY_WEIGHTS[item.priority] * -1, item.due_at))
        return rows

    def _priorities(
        self,
        *,
        intelligence: CareerIntelligenceResponse,
        followups: list[FollowUp],
        interviews: list[Interview],
        applications: list[JobApplication],
        companies: dict,
        today: date,
    ) -> list[PriorityItem]:
        rows: list[PriorityItem] = []
        pending = [
            item for item in followups if item.status == FollowUpStatus.PENDING.value
        ]
        overdue = [item for item in pending if item.due_date < today]
        due_today = [item for item in pending if item.due_date == today]
        soon_interviews = [
            item
            for item in interviews
            if item.scheduled_at.date() <= today + timedelta(days=2)
        ]

        for followup in overdue[:4]:
            rows.append(
                self._priority(
                    title=followup.title,
                    detail=f"Overdue since {followup.due_date.isoformat()}",
                    reason="Overdue follow-up",
                    priority="urgent",
                    source="followups",
                    due_at=datetime.combine(followup.due_date, time(hour=9), tzinfo=UTC),
                )
            )
        for followup in due_today[:4]:
            rows.append(
                self._priority(
                    title=followup.title,
                    detail="Due today",
                    reason="Today follow-up",
                    priority="high",
                    source="followups",
                    due_at=datetime.combine(followup.due_date, time(hour=9), tzinfo=UTC),
                )
            )
        app_by_id = {app.id: app for app in applications}
        for interview in soon_interviews[:3]:
            app = app_by_id.get(interview.application_id)
            company = companies.get(app.company_id) if app else None
            rows.append(
                self._priority(
                    title=f"Prepare for {app.job_title if app else 'interview'}",
                    detail=(
                        f"{interview.interview_type or 'Interview'} at "
                        f"{company.name if company else 'tracked company'}"
                    ),
                    reason="Interview within 48 hours",
                    priority="urgent",
                    source="interviews",
                    due_at=interview.scheduled_at,
                )
            )

        best_resume = intelligence.resume_insights.highest_interview_rate
        if best_resume:
            rows.append(
                self._priority(
                    title="Review strongest resume version",
                    detail=f"{best_resume.name} v{best_resume.version}",
                    reason=f"{best_resume.interview_rate}% interview rate",
                    priority="medium",
                    source="career_intelligence",
                )
            )

        top_skill = (
            intelligence.skill_intelligence.most_requested_skills[0]
            if intelligence.skill_intelligence.most_requested_skills
            else None
        )
        if top_skill:
            rows.append(
                self._priority(
                    title=f"Sharpen {top_skill.name} positioning",
                    detail=f"Appears in {top_skill.count} stored job descriptions",
                    reason="Top requested skill",
                    priority="medium",
                    source="career_intelligence",
                )
            )

        if not rows:
            rows.append(
                self._priority(
                    title="Add fresh job-search activity",
                    detail="Create applications, sync Gmail, or schedule follow-ups.",
                    reason="No urgent deadlines found",
                    priority="low",
                    source="copilot",
                )
            )

        rows.sort(
            key=lambda item: (
                -PRIORITY_WEIGHTS[item.priority],
                item.due_at or datetime.max.replace(tzinfo=UTC),
            )
        )
        return [
            item.model_copy(update={"rank": idx + 1}) for idx, item in enumerate(rows)
        ]

    @staticmethod
    def _priority(
        *,
        title: str,
        detail: str,
        reason: str,
        priority: str,
        source: str,
        due_at: datetime | None = None,
    ) -> PriorityItem:
        return PriorityItem(
            id=f"{source}-{_stable_id(title, detail, reason)}",
            rank=0,
            title=title,
            detail=detail,
            reason=reason,
            priority=priority,
            source=source,
            due_at=due_at,
        )

    @staticmethod
    def _timeline(
        deadlines: list[DeadlineItem], emails: list[GmailActivityItem]
    ) -> list[TimelineItem]:
        rows = [
            TimelineItem(
                id=item.id,
                kind=item.kind,
                title=item.title,
                subtitle=item.subtitle,
                timestamp=item.due_at,
            )
            for item in deadlines
        ]
        rows.extend(
            TimelineItem(
                id=f"email-{item.id}",
                kind="email",
                title=item.subject,
                subtitle=item.sender,
                timestamp=item.sent_at,
            )
            for item in emails
        )
        rows.sort(key=lambda item: item.timestamp)
        return rows

    @staticmethod
    def _skill_focus(intelligence: CareerIntelligenceResponse) -> list[SkillFocus]:
        rows = []
        for item in intelligence.skill_intelligence.most_requested_skills[:5]:
            rows.append(
                SkillFocus(
                    skill=item.name,
                    count=item.count,
                    percentage=item.percentage,
                    reason="Most requested in stored job descriptions",
                )
            )
        return rows

    @staticmethod
    def _resume_recommendation(
        intelligence: CareerIntelligenceResponse,
    ) -> ResumeRecommendation | None:
        best = intelligence.resume_insights.highest_interview_rate
        if best is None:
            return None
        return ResumeRecommendation(
            title=f"Use {best.name} v{best.version} as your baseline",
            detail=(
                "This linked resume version has the strongest observed interview "
                "conversion in your tracked applications."
            ),
            evidence=(
                f"{best.interview_rate}% interview rate across "
                f"{best.submitted_applications} applications"
            ),
        )

    @staticmethod
    def _interview_reminder(
        interviews: list[Interview], app_by_id: dict, today: date
    ) -> Reminder:
        if not interviews:
            return Reminder(
                title="Interview preparation",
                detail="No upcoming interviews are scheduled.",
                severity="low",
            )
        next_interview = interviews[0]
        app = app_by_id.get(next_interview.application_id)
        days = (next_interview.scheduled_at.date() - today).days
        severity = "urgent" if days <= 1 else "high" if days <= 3 else "medium"
        return Reminder(
            title="Interview preparation",
            detail=(
                f"Prepare for {app.job_title if app else 'your next interview'} "
                f"on {next_interview.scheduled_at.date().isoformat()}."
            ),
            due_date=next_interview.scheduled_at.date(),
            severity=severity,
        )

    @staticmethod
    def _followup_reminder(followups: list[FollowUp], today: date) -> Reminder:
        pending = [
            item for item in followups if item.status == FollowUpStatus.PENDING.value
        ]
        if not pending:
            return Reminder(
                title="Follow-up reminder",
                detail="No pending follow-ups are due.",
                severity="low",
            )
        next_followup = min(pending, key=lambda item: item.due_date)
        overdue_count = sum(1 for item in pending if item.due_date < today)
        due_today_count = sum(1 for item in pending if item.due_date == today)
        if overdue_count:
            detail = f"{overdue_count} follow-up{'s are' if overdue_count != 1 else ' is'} overdue."
            severity = "urgent"
        elif due_today_count:
            suffix = "s are" if due_today_count != 1 else " is"
            detail = f"{due_today_count} follow-up{suffix} due today."
            severity = "high"
        else:
            detail = f"Next follow-up is due {next_followup.due_date.isoformat()}."
            severity = "medium"
        return Reminder(
            title="Follow-up reminder",
            detail=detail,
            due_date=next_followup.due_date,
            severity=severity,
        )

    def _narrative(self, facts: dict) -> CopilotNarrative:
        fallback = self._fallback_narrative(facts)
        if self._insufficient_data(facts):
            return fallback
        try:
            prompt = render_template(
                PROMPT_TEMPLATE,
                {"briefing_json": json.dumps(facts, sort_keys=True)},
            )
            client = self._resolve_client(fallback)
            structured = client.generate_structured(
                GenerationRequest(
                    system=prompt.system,
                    prompt=prompt.user,
                    temperature=0.2,
                ),
                CopilotBriefingResult,
                db=self.db,
                feature=FEATURE,
                user_id=self.user_id,
            )
            result = structured.data
            return CopilotNarrative(
                available=True,
                provider=structured.result.provider,
                model=structured.result.model,
                executive_summary=result.executive_summary,
                ai_recommendations=result.ai_recommendations,
                skill_focus=result.skill_focus,
                resume_recommendation=result.resume_recommendation,
                interview_preparation_reminder=result.interview_preparation_reminder,
                follow_up_reminder=result.follow_up_reminder,
                caveats=result.caveats,
            )
        except AIError as exc:
            logger.warning("Career Copilot AI narrative unavailable: %s", exc)
            return fallback.model_copy(
                update={
                    "caveats": [
                        *fallback.caveats,
                        "AI narrative unavailable; showing deterministic briefing.",
                    ]
                }
            )

    def _resolve_client(self, fallback: CopilotNarrative) -> AIClient:
        if self._injected_client is not None:
            return self._injected_client
        if settings.ai_active_provider == "mock":
            payload = CopilotBriefingResult(
                executive_summary=fallback.executive_summary,
                ai_recommendations=fallback.ai_recommendations,
                skill_focus=fallback.skill_focus,
                resume_recommendation=fallback.resume_recommendation,
                interview_preparation_reminder=fallback.interview_preparation_reminder,
                follow_up_reminder=fallback.follow_up_reminder,
                caveats=fallback.caveats,
            )
            return AIClient(
                MockProvider(default_response=payload.model_dump_json()),
                default_model=settings.AI_MODEL,
            )
        return get_ai_client()

    @staticmethod
    def _fallback_narrative(facts: dict) -> CopilotNarrative:
        metrics = facts["today_metrics"]
        priorities = facts["top_priorities"]
        skills = facts["skill_focus"]
        resume = facts["resume_recommendation"]
        summary = (
            f"You have {metrics['active_applications']} active applications, "
            f"{metrics['followups_due_today']} follow-ups due today, and "
            f"{metrics['upcoming_interviews']} interviews in the next week."
        )
        recommendations = [
            item["title"] for item in priorities[:4]
        ] or ["Add applications, follow-ups, or interviews to build a daily plan."]
        return CopilotNarrative(
            available=False,
            executive_summary=summary,
            ai_recommendations=recommendations,
            skill_focus=(
                f"Focus on {skills[0]['skill']} today."
                if skills
                else "No stored job-description skill signal is available yet."
            ),
            resume_recommendation=(
                resume["title"] if resume else "No linked resume performance signal yet."
            ),
            interview_preparation_reminder=(
                "Review the next scheduled interview and open Interview Prep if needed."
            ),
            follow_up_reminder="Clear overdue and today follow-ups first.",
            caveats=[],
        )

    @staticmethod
    def _insufficient_data(facts: dict) -> bool:
        metrics = facts["today_metrics"]
        return (
            metrics["active_applications"] == 0
            and metrics["followups_due_today"] == 0
            and metrics["overdue_followups"] == 0
            and metrics["upcoming_interviews"] == 0
            and metrics["recent_emails"] == 0
        )

    @staticmethod
    def _deadline_priority(due_date: date, today: date) -> str:
        if due_date < today:
            return "urgent"
        if due_date == today:
            return "high"
        if due_date <= today + timedelta(days=2):
            return "medium"
        return "low"


def _stable_id(*parts: str) -> str:
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]
