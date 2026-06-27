from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.followups.model import FollowUp
from app.features.gmail.models import EmailMessage
from app.features.interviews.model import Interview


class CareerCopilotRepository:
    """Read-only queries for the Career Copilot daily briefing."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_applications(self) -> list[JobApplication]:
        return list(self.db.scalars(select(JobApplication)).all())

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company)).all())

    def list_followups(self) -> list[FollowUp]:
        return list(
            self.db.scalars(select(FollowUp).order_by(FollowUp.due_date.asc())).all()
        )

    def list_recent_emails(self, *, since: datetime, limit: int = 8) -> list[EmailMessage]:
        return list(
            self.db.scalars(
                select(EmailMessage)
                .where(EmailMessage.sent_at >= since)
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
                .where(Interview.scheduled_at >= now)
                .order_by(Interview.scheduled_at.asc())
                .limit(limit)
            ).all()
        )

