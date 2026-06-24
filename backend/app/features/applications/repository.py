import logging
from uuid import UUID

from sqlalchemy import func, nulls_last, select
from sqlalchemy.orm import Session

from app.features.applications.model import ApplicationStatus, JobApplication
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ApplicationRepository(BaseRepository[JobApplication]):
    def __init__(self, db: Session) -> None:
        super().__init__(JobApplication, db)

    def list_paginated(
        self,
        *,
        query: str | None = None,
        status: ApplicationStatus | None = None,
        company_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[JobApplication], int]:
        base = select(JobApplication)

        if query:
            base = base.where(JobApplication.job_title.ilike(f"%{query}%"))
        if status is not None:
            base = base.where(JobApplication.status == status.value)
        if company_id is not None:
            base = base.where(JobApplication.company_id == company_id)

        # Count with all filters applied before adding ORDER BY / pagination.
        # Using a subquery keeps the filter logic in one place.
        total = (
            self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        )

        items = list(
            self.db.scalars(
                base.order_by(
                    # Drafts (no date_applied) sink to the bottom; among applied
                    # entries the most recent activity appears first.
                    nulls_last(JobApplication.date_applied.desc()),
                    JobApplication.created_at.desc(),
                )
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total
