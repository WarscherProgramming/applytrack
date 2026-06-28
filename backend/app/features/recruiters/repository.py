import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.recruiters.model import Recruiter
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RecruiterRepository(BaseRepository[Recruiter]):
    def __init__(self, db: Session) -> None:
        super().__init__(Recruiter, db)

    def get_by_email(self, email: str, user_id: UUID) -> Recruiter | None:
        stmt = select(Recruiter).where(Recruiter.email == email, Recruiter.user_id == user_id)
        return self.db.scalars(stmt).first()

    def list_paginated(
        self,
        *,
        query: str | None = None,
        company_id: UUID | None = None,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Recruiter], int]:
        base = select(Recruiter).where(Recruiter.user_id == user_id)

        if query:
            pattern = f"%{query}%"
            # OR across all searchable text columns so a single query param
            # matches on name, email, or job title without separate endpoints.
            base = base.where(
                or_(
                    Recruiter.first_name.ilike(pattern),
                    Recruiter.last_name.ilike(pattern),
                    Recruiter.email.ilike(pattern),
                    Recruiter.title.ilike(pattern),
                )
            )
        if company_id is not None:
            base = base.where(Recruiter.company_id == company_id)

        # Subquery count keeps filter logic in one place — no risk of
        # the count query drifting from the data query.
        total = (
            self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        )

        items = list(
            self.db.scalars(
                base.order_by(Recruiter.created_at.desc()).offset(skip).limit(limit)
            ).all()
        )
        return items, total
