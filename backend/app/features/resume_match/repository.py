from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.resume_match.model import ResumeMatchAnalysis
from app.shared.base_repository import BaseRepository


class ResumeMatchRepository(BaseRepository[ResumeMatchAnalysis]):
    def __init__(self, db: Session) -> None:
        super().__init__(ResumeMatchAnalysis, db)

    def list_paginated(
        self,
        *,
        resume_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ResumeMatchAnalysis], int]:
        base = select(ResumeMatchAnalysis)
        if resume_id is not None:
            base = base.where(ResumeMatchAnalysis.resume_id == resume_id)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        items = list(
            self.db.scalars(
                # Newest analyses first — history reads as a reverse-chronological
                # feed.
                base.order_by(ResumeMatchAnalysis.created_at.desc())
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total
