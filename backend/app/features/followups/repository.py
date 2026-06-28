import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.followups.model import (
    FollowUp,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class FollowUpRepository(BaseRepository[FollowUp]):
    def __init__(self, db: Session) -> None:
        super().__init__(FollowUp, db)

    def list_paginated(
        self,
        *,
        application_id: UUID | None = None,
        recruiter_id: UUID | None = None,
        interview_id: UUID | None = None,
        status: FollowUpStatus | None = None,
        priority: FollowUpPriority | None = None,
        followup_type: FollowUpType | None = None,
        overdue: bool = False,
        due_today: bool = False,
        due_this_week: bool = False,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[FollowUp], int]:
        base = select(FollowUp).where(FollowUp.user_id == user_id)

        if application_id is not None:
            base = base.where(FollowUp.application_id == application_id)
        if recruiter_id is not None:
            base = base.where(FollowUp.recruiter_id == recruiter_id)
        if interview_id is not None:
            base = base.where(FollowUp.interview_id == interview_id)
        if status is not None:
            base = base.where(FollowUp.status == status.value)
        if priority is not None:
            base = base.where(FollowUp.priority == priority.value)
        if followup_type is not None:
            base = base.where(FollowUp.followup_type == followup_type.value)

        # Date-window reminders are scoped to PENDING items only: a completed or
        # skipped follow-up is no longer an actionable reminder, so it should not
        # surface in "overdue", "today", or "this week" views. "today" is in UTC.
        today = datetime.now(timezone.utc).date()
        if overdue:
            base = base.where(
                FollowUp.due_date < today,
                FollowUp.status == FollowUpStatus.PENDING.value,
            )
        if due_today:
            base = base.where(
                FollowUp.due_date == today,
                FollowUp.status == FollowUpStatus.PENDING.value,
            )
        if due_this_week:
            # Rolling 7-day window: today through 6 days out (inclusive).
            base = base.where(
                FollowUp.due_date >= today,
                FollowUp.due_date <= today + timedelta(days=6),
                FollowUp.status == FollowUpStatus.PENDING.value,
            )

        # Subquery count keeps every filter in one place — the count query can
        # never drift out of sync with the data query.
        total = (
            self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        )

        items = list(
            self.db.scalars(
                # ASC: the soonest-due follow-up appears first, making the list
                # a prioritised to-do queue.
                base.order_by(FollowUp.due_date.asc())
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total
