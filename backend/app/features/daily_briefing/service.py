from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.ai.errors import AIError
from app.core.config import settings
from app.exceptions.http import NotFoundError
from app.features.career_copilot.service import CareerCopilotService
from app.features.career_intelligence.service import CareerIntelligenceService
from app.features.daily_briefing.model import (
    Notification,
    NotificationCategory,
    NotificationPriority,
)
from app.features.daily_briefing.repository import DailyBriefingRepository
from app.features.daily_briefing.schemas import (
    BriefingItem,
    DailyBriefingAI,
    DailyBriefingAIResult,
    DailyBriefingResponse,
    NotificationListResponse,
    NotificationResponse,
    NotificationUpdate,
    OpportunityHighlight,
    RecruiterEmailItem,
    ResumePerformanceChange,
    SkillTrendUpdate,
)
from app.features.followups.model import FollowUp
from app.features.gmail.models import EmailMessage
from app.features.interviews.model import Interview
from app.features.job_intelligence.service import JobIntelligenceService

logger = logging.getLogger(__name__)

FEATURE = "daily_briefing"
PROMPT_TEMPLATE = "daily_briefing.v1"
PRIORITY_ORDER = {
    NotificationPriority.URGENT: 4,
    NotificationPriority.HIGH: 3,
    NotificationPriority.MEDIUM: 2,
    NotificationPriority.LOW: 1,
}


class DailyBriefingService:
    """Builds the proactive briefing and owns notification lifecycle actions."""

    def __init__(self, db: Session, user_id: UUID, *, ai_client: AIClient | None = None) -> None:
        self.db = db
        self.user_id = user_id
        self.repo = DailyBriefingRepository(db, user_id)
        self._injected_client = ai_client

    def build_briefing(self) -> DailyBriefingResponse:
        now = datetime.now(UTC)
        today = now.date()
        since = now - timedelta(days=1)

        copilot = CareerCopilotService(self.db, self.user_id).build_daily_briefing()
        career = CareerIntelligenceService(self.db, self.user_id).build_dashboard()
        job_intelligence = JobIntelligenceService(self.db, self.user_id).build_report()

        applications = self.repo.list_applications()
        companies = self.repo.list_companies()
        company_by_id = {company.id: company for company in companies}
        app_by_id = {app.id: app for app in applications}

        due_today = [
            self._followup_item(item, today=today, overdue=False)
            for item in self.repo.list_followups_due_today(today)
        ]
        overdue = [
            self._followup_item(item, today=today, overdue=True)
            for item in self.repo.list_overdue_followups(today)
        ]
        upcoming_interviews = [
            self._interview_item(item, app_by_id)
            for item in self.repo.list_upcoming_interviews(
                now=now, until=now + timedelta(days=7)
            )
        ]
        recruiter_emails = [
            self._email_item(item)
            for item in self.repo.list_recent_recruiter_emails(since)
            if _looks_recruiting_related(item)
        ]
        opportunities = [
            OpportunityHighlight(
                id=app.id,
                company=company_by_id[app.company_id].name
                if app.company_id in company_by_id
                else "Unknown company",
                title=app.job_title,
                created_at=app.created_at,
                source=app.source,
                job_url=app.job_link,
            )
            for app in self.repo.list_recent_opportunity_applications(since)
        ]
        resume_changes = self._resume_performance(career)
        skill_updates = [
            SkillTrendUpdate(
                skill=signal.name,
                category=signal.category,
                frequency=signal.frequency,
                trend_delta=signal.trend_delta,
                percentage=signal.percentage,
            )
            for signal in job_intelligence.skill_signals
            if signal.trend_delta > 0
        ][:5]

        prioritized_actions = self._prioritized_actions(
            overdue=overdue,
            due_today=due_today,
            interviews=upcoming_interviews,
            recruiter_emails=recruiter_emails,
            opportunities=opportunities,
            copilot_actions=[
                BriefingItem(
                    id=item.id,
                    title=item.title,
                    detail=item.detail,
                    priority=NotificationPriority(item.priority),
                    category=NotificationCategory.AI_INSIGHT,
                    due_at=item.due_at,
                    action_url=None,
                )
                for item in copilot.deterministic_priorities
            ],
        )

        self._sync_notifications(
            due_today=due_today,
            overdue=overdue,
            interviews=upcoming_interviews,
            recruiter_emails=recruiter_emails,
            opportunities=opportunities,
            skill_updates=skill_updates,
            ai_recommendations=copilot.briefing.ai_recommendations,
        )
        pinned, _ = self.repo.list_notifications(pinned_only=True, limit=10)
        facts = {
            "date": today.isoformat(),
            "followups_due_today": [item.model_dump(mode="json") for item in due_today],
            "overdue_followups": [item.model_dump(mode="json") for item in overdue],
            "upcoming_interviews": [
                item.model_dump(mode="json") for item in upcoming_interviews
            ],
            "new_recruiter_emails": [
                item.model_dump(mode="json") for item in recruiter_emails[:5]
            ],
            "newly_discovered_opportunities": [
                item.model_dump(mode="json") for item in opportunities[:5]
            ],
            "resume_performance_changes": [
                item.model_dump(mode="json") for item in resume_changes
            ],
            "skill_trend_updates": [
                item.model_dump(mode="json") for item in skill_updates
            ],
            "prioritized_actions": [
                item.model_dump(mode="json") for item in prioritized_actions[:8]
            ],
        }
        narrative = self._narrative(facts)
        return DailyBriefingResponse(
            generated_at=datetime.now(UTC),
            briefing_date=today,
            morning_summary=narrative.morning_summary,
            followups_due_today=due_today,
            overdue_followups=overdue,
            upcoming_interviews=upcoming_interviews,
            new_recruiter_emails=recruiter_emails,
            newly_discovered_opportunities=opportunities,
            resume_performance_changes=resume_changes,
            skill_trend_updates=skill_updates,
            ai_recommendations=narrative.recommendations,
            prioritized_actions=prioritized_actions[:10],
            pinned_notifications=[NotificationResponse.model_validate(item) for item in pinned],
            unread_notification_count=self.repo.count_unread(),
            ai_narrative=narrative,
        )

    def list_notifications(
        self,
        *,
        include_dismissed: bool = False,
        unread_only: bool = False,
        pinned_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> NotificationListResponse:
        items, total = self.repo.list_notifications(
            include_dismissed=include_dismissed,
            unread_only=unread_only,
            pinned_only=pinned_only,
            skip=skip,
            limit=limit,
        )
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(item) for item in items],
            total=total,
            unread_count=self.repo.count_unread(),
            pinned_count=self.repo.count_pinned(),
        )

    def update_notification(
        self, notification_id: UUID, data: NotificationUpdate
    ) -> Notification:
        notification = self.repo.get_notification(notification_id)
        if notification is None:
            raise NotFoundError("Notification", notification_id)
        return self.repo.update_notification(
            notification, data.model_dump(exclude_unset=True)
        )

    @staticmethod
    def _followup_item(
        followup: FollowUp, *, today: date, overdue: bool
    ) -> BriefingItem:
        due_at = datetime.combine(followup.due_date, time(hour=9), tzinfo=UTC)
        priority = (
            NotificationPriority.URGENT
            if overdue or followup.priority == "urgent"
            else NotificationPriority(followup.priority)
        )
        detail = (
            f"Overdue since {followup.due_date.isoformat()}"
            if overdue
            else "Due today"
        )
        if followup.description:
            detail = f"{detail}: {followup.description}"
        return BriefingItem(
            id=f"followup-{followup.id}",
            title=followup.title,
            detail=detail,
            priority=priority,
            category=NotificationCategory.FOLLOW_UP,
            due_at=due_at,
            action_url="/followups",
        )

    @staticmethod
    def _interview_item(interview: Interview, app_by_id: dict) -> BriefingItem:
        app = app_by_id.get(interview.application_id)
        title = f"Prepare for {app.job_title if app else 'interview'}"
        detail = interview.interview_type or "Interview"
        if interview.location or interview.meeting_link:
            detail = f"{detail} - {interview.location or interview.meeting_link}"
        return BriefingItem(
            id=f"interview-{interview.id}",
            title=title,
            detail=detail,
            priority=NotificationPriority.HIGH,
            category=NotificationCategory.INTERVIEW,
            due_at=interview.scheduled_at,
            action_url="/interviews",
        )

    @staticmethod
    def _email_item(email: EmailMessage) -> RecruiterEmailItem:
        return RecruiterEmailItem(
            id=email.id,
            subject=email.subject or "(no subject)",
            sender=email.sender,
            sent_at=email.sent_at,
            match_reason=email.match_reason,
        )

    @staticmethod
    def _resume_performance(career) -> list[ResumePerformanceChange]:
        rows = []
        best = career.resume_insights.highest_interview_rate
        if best is not None:
            rows.append(
                ResumePerformanceChange(
                    title=f"{best.name} v{best.version} is your strongest interview resume",
                    detail="Highest interview-rate resume in tracked applications.",
                    evidence=(
                        f"{best.interview_rate}% across "
                        f"{best.submitted_applications} applications"
                    ),
                )
            )
        response = career.resume_insights.highest_response_rate
        if response is not None and (best is None or response.id != best.id):
            rows.append(
                ResumePerformanceChange(
                    title=f"{response.name} v{response.version} has the best response rate",
                    detail="Highest response-rate resume in tracked applications.",
                    evidence=f"{response.response_rate}% response rate",
                )
            )
        return rows

    @staticmethod
    def _prioritized_actions(
        *,
        overdue: list[BriefingItem],
        due_today: list[BriefingItem],
        interviews: list[BriefingItem],
        recruiter_emails: list[RecruiterEmailItem],
        opportunities: list[OpportunityHighlight],
        copilot_actions: list[BriefingItem],
    ) -> list[BriefingItem]:
        rows = [*overdue, *due_today, *interviews]
        rows.extend(
            BriefingItem(
                id=f"email-{email.id}",
                title=f"Review recruiter email from {email.sender}",
                detail=email.subject,
                priority=NotificationPriority.MEDIUM,
                category=NotificationCategory.GMAIL,
                due_at=email.sent_at,
                action_url="/settings",
            )
            for email in recruiter_emails[:3]
        )
        rows.extend(
            BriefingItem(
                id=f"opportunity-{item.id}",
                title=f"Review discovered role: {item.title}",
                detail=item.company,
                priority=NotificationPriority.MEDIUM,
                category=NotificationCategory.OPPORTUNITY,
                due_at=item.created_at,
                action_url="/applications",
            )
            for item in opportunities[:3]
        )
        rows.extend(copilot_actions)
        unique = {item.id: item for item in rows}
        ordered = sorted(
            unique.values(),
            key=lambda item: (
                -PRIORITY_ORDER[item.priority],
                item.due_at or datetime.max.replace(tzinfo=UTC),
            ),
        )
        return [
            item.model_copy(update={"id": f"action-{index + 1}-{_stable_id(item.id)}"})
            for index, item in enumerate(ordered)
        ]

    def _sync_notifications(
        self,
        *,
        due_today: list[BriefingItem],
        overdue: list[BriefingItem],
        interviews: list[BriefingItem],
        recruiter_emails: list[RecruiterEmailItem],
        opportunities: list[OpportunityHighlight],
        skill_updates: list[SkillTrendUpdate],
        ai_recommendations: list[str],
    ) -> None:
        for item in [*overdue, *due_today, *interviews]:
            self._upsert_item_notification(item)
        for email in recruiter_emails[:10]:
            self.repo.upsert_notification(
                {
                    "title": f"New recruiter email from {email.sender}",
                    "message": email.subject,
                    "category": NotificationCategory.GMAIL.value,
                    "priority": NotificationPriority.MEDIUM.value,
                    "source_type": "email",
                    "source_id": str(email.id),
                    "action_url": "/settings",
                    "dedupe_key": f"email:{email.id}",
                }
            )
        for opportunity in opportunities[:10]:
            self.repo.upsert_notification(
                {
                    "title": f"New opportunity saved: {opportunity.title}",
                    "message": opportunity.company,
                    "category": NotificationCategory.OPPORTUNITY.value,
                    "priority": NotificationPriority.MEDIUM.value,
                    "source_type": "application",
                    "source_id": str(opportunity.id),
                    "action_url": "/applications",
                    "dedupe_key": f"opportunity:{opportunity.id}",
                }
            )
        for skill in skill_updates[:5]:
            self.repo.upsert_notification(
                {
                    "title": f"{skill.skill} is trending in saved jobs",
                    "message": f"Trend delta +{skill.trend_delta}; {skill.frequency} mentions.",
                    "category": NotificationCategory.AI_INSIGHT.value,
                    "priority": NotificationPriority.LOW.value,
                    "source_type": "job_intelligence",
                    "source_id": skill.skill,
                    "action_url": "/job-intelligence",
                    "dedupe_key": f"skill:{skill.skill}:{skill.trend_delta}",
                }
            )
        for recommendation in ai_recommendations[:3]:
            self.repo.upsert_notification(
                {
                    "title": "AI insight",
                    "message": recommendation,
                    "category": NotificationCategory.AI_INSIGHT.value,
                    "priority": NotificationPriority.LOW.value,
                    "source_type": "daily_briefing",
                    "source_id": None,
                    "action_url": "/daily-briefing",
                    "dedupe_key": f"ai:{_stable_id(recommendation)}",
                }
            )

    def _upsert_item_notification(self, item: BriefingItem) -> None:
        self.repo.upsert_notification(
            {
                "title": item.title,
                "message": item.detail,
                "category": (item.category or NotificationCategory.AI_INSIGHT).value,
                "priority": item.priority.value,
                "source_type": item.category.value if item.category else "briefing",
                "source_id": item.id,
                "action_url": item.action_url,
                "dedupe_key": item.id,
            }
        )

    def _narrative(self, facts: dict) -> DailyBriefingAI:
        fallback = _fallback_narrative(facts)
        try:
            prompt = render_template(
                PROMPT_TEMPLATE,
                {"daily_briefing_json": json.dumps(facts, sort_keys=True)},
            )
            client = self._resolve_client(fallback)
            structured = client.generate_structured(
                GenerationRequest(system=prompt.system, prompt=prompt.user, temperature=0.2),
                DailyBriefingAIResult,
                db=self.db,
                feature=FEATURE,
                user_id=self.user_id,
            )
            result = structured.data
            return DailyBriefingAI(
                available=True,
                provider=structured.result.provider,
                model=structured.result.model,
                morning_summary=result.morning_summary,
                recommendations=result.recommendations,
                caveats=result.caveats,
            )
        except AIError as exc:
            logger.warning("Daily Briefing AI narrative unavailable: %s", exc)
            return fallback.model_copy(
                update={
                    "caveats": [
                        *fallback.caveats,
                        "AI narrative unavailable; showing deterministic briefing.",
                    ]
                }
            )

    def _resolve_client(self, fallback: DailyBriefingAI) -> AIClient:
        if self._injected_client is not None:
            return self._injected_client
        if settings.ai_active_provider == "mock":
            payload = DailyBriefingAIResult(
                morning_summary=fallback.morning_summary,
                recommendations=fallback.recommendations,
                caveats=fallback.caveats,
            )
            return AIClient(
                MockProvider(default_response=payload.model_dump_json()),
                default_model=settings.AI_MODEL,
            )
        return get_ai_client()


def _fallback_narrative(facts: dict) -> DailyBriefingAI:
    overdue = len(facts["overdue_followups"])
    due = len(facts["followups_due_today"])
    interviews = len(facts["upcoming_interviews"])
    emails = len(facts["new_recruiter_emails"])
    summary = (
        f"Today has {due} follow-ups due, {overdue} overdue follow-ups, "
        f"{interviews} upcoming interviews, and {emails} new recruiter emails."
    )
    recommendations = [
        item["title"] for item in facts["prioritized_actions"][:4]
    ] or ["Add follow-ups, interviews, Gmail, or opportunities to build a briefing."]
    return DailyBriefingAI(
        available=False,
        morning_summary=summary,
        recommendations=recommendations,
        caveats=[],
    )


def _looks_recruiting_related(email: EmailMessage) -> bool:
    haystack = f"{email.subject or ''} {email.sender} {email.match_reason or ''}".lower()
    return any(
        token in haystack
        for token in ("recruit", "talent", "interview", "application", "hiring")
    )


def _stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
