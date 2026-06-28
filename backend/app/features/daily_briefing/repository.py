from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.daily_briefing.model import Notification
from app.features.followups.model import FollowUp, FollowUpStatus
from app.features.gmail.models import EmailMessage
from app.features.interviews.model import Interview, InterviewStatus


class DailyBriefingRepository:
    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def list_followups_due_today(self, today: date) -> list[FollowUp]:
        return list(
            self.db.scalars(
                select(FollowUp)
                .where(
                    FollowUp.status == FollowUpStatus.PENDING.value,
                    FollowUp.due_date == today,
                    FollowUp.user_id == self.user_id,
                )
                .order_by(FollowUp.priority.desc(), FollowUp.created_at.asc())
            ).all()
        )

    def list_overdue_followups(self, today: date) -> list[FollowUp]:
        return list(
            self.db.scalars(
                select(FollowUp)
                .where(
                    FollowUp.status == FollowUpStatus.PENDING.value,
                    FollowUp.due_date < today,
                    FollowUp.user_id == self.user_id,
                )
                .order_by(FollowUp.due_date.asc())
            ).all()
        )

    def list_upcoming_interviews(self, *, now: datetime, until: datetime) -> list[Interview]:
        return list(
            self.db.scalars(
                select(Interview)
                .where(
                    Interview.status == InterviewStatus.SCHEDULED.value,
                    Interview.scheduled_at >= now,
                    Interview.scheduled_at <= until,
                    Interview.user_id == self.user_id,
                )
                .order_by(Interview.scheduled_at.asc())
            ).all()
        )

    def list_recent_recruiter_emails(self, since: datetime) -> list[EmailMessage]:
        return list(
            self.db.scalars(
                select(EmailMessage)
                .where(
                    EmailMessage.sent_at >= since,
                    EmailMessage.direction == "inbound",
                    EmailMessage.user_id == self.user_id,
                )
                .order_by(EmailMessage.sent_at.desc())
                .limit(25)
            ).all()
        )

    def list_recent_opportunity_applications(self, since: datetime) -> list[JobApplication]:
        return list(
            self.db.scalars(
                select(JobApplication)
                .where(
                    JobApplication.created_at >= since,
                    JobApplication.source.ilike("Opportunity Discovery:%"),
                    JobApplication.user_id == self.user_id,
                )
                .order_by(JobApplication.created_at.desc())
            ).all()
        )

    def list_applications(self) -> list[JobApplication]:
        return list(
            self.db.scalars(
                select(JobApplication).where(JobApplication.user_id == self.user_id)
            ).all()
        )

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company).where(Company.user_id == self.user_id)).all())

    def get_notification(self, notification_id: UUID) -> Notification | None:
        return self.db.scalars(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == self.user_id,
            )
        ).first()

    def get_notification_by_dedupe_key(self, dedupe_key: str) -> Notification | None:
        return self.db.scalars(
            select(Notification).where(
                Notification.dedupe_key == dedupe_key,
                Notification.user_id == self.user_id,
            )
        ).first()

    def upsert_notification(self, data: dict) -> Notification:
        existing = self.get_notification_by_dedupe_key(data["dedupe_key"])
        if existing is not None:
            for key in ("title", "message", "priority", "action_url"):
                setattr(existing, key, data[key])
            self.db.flush()
            return existing
        notification = Notification(**(data | {"user_id": self.user_id}))
        self.db.add(notification)
        self.db.flush()
        return notification

    def update_notification(self, notification: Notification, data: dict) -> Notification:
        for key, value in data.items():
            setattr(notification, key, value)
        self.db.flush()
        return notification

    def list_notifications(
        self,
        *,
        include_dismissed: bool = False,
        unread_only: bool = False,
        pinned_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == self.user_id)
        if not include_dismissed:
            base = base.where(Notification.is_dismissed.is_(False))
        if unread_only:
            base = base.where(Notification.is_read.is_(False))
        if pinned_only:
            base = base.where(Notification.is_pinned.is_(True))
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.order_by(
                    Notification.is_pinned.desc(),
                    Notification.is_read.asc(),
                    Notification.created_at.desc(),
                )
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total

    def count_unread(self) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.is_read.is_(False),
                Notification.is_dismissed.is_(False),
                Notification.user_id == self.user_id,
            )
        ) or 0

    def count_pinned(self) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.is_pinned.is_(True),
                Notification.is_dismissed.is_(False),
                Notification.user_id == self.user_id,
            )
        ) or 0
