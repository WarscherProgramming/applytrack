import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from uuid import UUID

from app.features.companies.model import Company
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session) -> None:
        super().__init__(Company, db)

    def get_by_name(self, name: str, user_id: UUID) -> Company | None:
        stmt = select(Company).where(Company.name == name, Company.user_id == user_id)
        return self.db.scalars(stmt).first()

    def get_all_paginated(
        self, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[list[Company], int]:
        base = select(Company).where(Company.user_id == user_id)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.order_by(Company.name).offset(skip).limit(limit)
            ).all()
        )
        return items, total

    def search(
        self, query: str, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[list[Company], int]:
        pattern = f"%{query}%"
        base = select(Company).where(Company.user_id == user_id, Company.name.ilike(pattern))
        total = (
            self.db.scalar(
                select(func.count()).select_from(base.subquery())
            )
            or 0
        )
        items = list(
            self.db.scalars(
                base.order_by(Company.name).offset(skip).limit(limit)
            ).all()
        )
        return items, total
