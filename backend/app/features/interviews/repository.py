import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.interviews.model import Interview, InterviewStatus, InterviewType
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class InterviewRepository(BaseRepository[Interview]):
    def __init__(self, db: Session) -> None:
        super().__init__(Interview, db)

    def list_paginated(
        self,
        *,
        application_id: UUID | None = None,
        recruiter_id: UUID | None = None,
        status: InterviewStatus | None = None,
        interview_type: InterviewType | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Interview], int]:
        base = select(Interview)

        if application_id is not None:
            base = base.where(Interview.application_id == application_id)
        if recruiter_id is not None:
            base = base.where(Interview.recruiter_id == recruiter_id)
        if status is not None:
            base = base.where(Interview.status == status.value)
        if interview_type is not None:
            base = base.where(Interview.interview_type == interview_type.value)

        # Subquery count keeps filters in one place; no risk of the count
        # query drifting out of sync with the data query.
        total = (
            self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        )

        items = list(
            self.db.scalars(
                # ASC: upcoming interviews appear first, making the list an
                # agenda-style view of what's coming next.
                base.order_by(Interview.scheduled_at.asc())
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total
