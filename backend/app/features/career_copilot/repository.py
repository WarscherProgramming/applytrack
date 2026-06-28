from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.followups.model import FollowUp
from app.features.gmail.models import EmailMessage
from app.features.interviews.model import Interview


class CareerCopilotRepository:
    """Read-only queries for the Career Copilot daily briefing."""

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def list_applications(self) -> list[JobApplication]:
        return list(
            self.db.scalars(
                select(JobApplication).where(JobApplication.user_id == self.user_id)
            ).all()
        )

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company).where(Company.user_id == self.user_id)).all())

    def list_followups(self) -> list[FollowUp]:
        return list(
            self.db.scalars(
                select(FollowUp)
                .where(FollowUp.user_id == self.user_id)
                .order_by(FollowUp.due_date.asc())
            ).all()
        )

    def list_recent_emails(self, *, since: datetime, limit: int = 8) -> list[EmailMessage]:
        return list(
            self.db.scalars(
                select(EmailMessage)
                .where(
                    EmailMessage.sent_at >= since,
                    EmailMessage.user_id == self.user_id,
                )
                .order_by(EmailMessage.sent_at.desc())
                .limit(limit)
            ).all()
        )

    def list_upcoming_interviews(
        self, *, now: datetime, limit: int = 8
    ) -> list[Interview]:
        return list(
            self.db.scalars(
                select(Interview)
                .where(
                    Interview.scheduled_at >= now,
                    Interview.user_id == self.user_id,
                )
                .order_by(Interview.scheduled_at.asc())
                .limit(limit)
            ).all()
        )

