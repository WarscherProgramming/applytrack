from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.interview_ai.model import InterviewPrepPackage
from app.shared.base_repository import BaseRepository


class InterviewPrepRepository(BaseRepository[InterviewPrepPackage]):
    def __init__(self, db: Session) -> None:
        super().__init__(InterviewPrepPackage, db)

    def list_paginated(
        self,
        *,
        application_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[InterviewPrepPackage], int]:
        base = select(InterviewPrepPackage)
        if application_id is not None:
            base = base.where(InterviewPrepPackage.application_id == application_id)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        items = list(
            self.db.scalars(
                # Newest first — history reads as a reverse-chronological feed.
                base.order_by(InterviewPrepPackage.created_at.desc())
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total
