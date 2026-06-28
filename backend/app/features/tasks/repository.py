from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, nulls_last, select
from sqlalchemy.orm import Session

from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.followups.model import FollowUp, FollowUpStatus
from app.features.gmail.models import EmailMessage
from app.features.interviews.model import Interview, InterviewStatus
from app.features.tasks.model import Task, TaskPriority, TaskSource, TaskStatus
from app.shared.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session) -> None:
        super().__init__(Task, db)

    def list_paginated(
        self,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        source: TaskSource | None = None,
        application_id: UUID | None = None,
        company_id: UUID | None = None,
        recruiter_id: UUID | None = None,
        interview_id: UUID | None = None,
        followup_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        base = select(Task)
        if status is not None:
            base = base.where(Task.status == status.value)
        if priority is not None:
            base = base.where(Task.priority == priority.value)
        if source is not None:
            base = base.where(Task.source == source.value)
        if application_id is not None:
            base = base.where(Task.application_id == application_id)
        if company_id is not None:
            base = base.where(Task.company_id == company_id)
        if recruiter_id is not None:
            base = base.where(Task.recruiter_id == recruiter_id)
        if interview_id is not None:
            base = base.where(Task.interview_id == interview_id)
        if followup_id is not None:
            base = base.where(Task.followup_id == followup_id)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.order_by(
                    Task.status.asc(),
                    nulls_last(Task.due_date.asc()),
                    Task.priority.desc(),
                    Task.created_at.desc(),
                )
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total

    def get_by_source_key(self, source_key: str) -> Task | None:
        return self.db.scalars(select(Task).where(Task.source_key == source_key)).first()

    def list_overdue_followups(self, today: date) -> list[FollowUp]:
        return list(
            self.db.scalars(
                select(FollowUp)
                .where(
                    FollowUp.status == FollowUpStatus.PENDING.value,
                    FollowUp.due_date < today,
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
                )
                .order_by(Interview.scheduled_at.asc())
            ).all()
        )

    def list_unread_recruiter_emails(self) -> list[EmailMessage]:
        return list(
            self.db.scalars(
                select(EmailMessage)
                .where(
                    EmailMessage.direction == "inbound",
                    EmailMessage.labels.contains(["UNREAD"]),
                )
                .order_by(EmailMessage.sent_at.desc())
                .limit(25)
            ).all()
        )

    def list_applications(self) -> list[JobApplication]:
        return list(self.db.scalars(select(JobApplication)).all())

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company)).all())
