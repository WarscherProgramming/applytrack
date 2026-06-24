import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.companies.model import Company
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session) -> None:
        super().__init__(Company, db)

    def get_by_name(self, name: str) -> Company | None:
        stmt = select(Company).where(Company.name == name)
        return self.db.scalars(stmt).first()

    def get_all_paginated(
        self, *, skip: int = 0, limit: int = 100
    ) -> tuple[list[Company], int]:
        total = self.db.scalar(select(func.count()).select_from(Company)) or 0
        items = list(
            self.db.scalars(
                select(Company).order_by(Company.name).offset(skip).limit(limit)
            ).all()
        )
        return items, total

    def search(
        self, query: str, *, skip: int = 0, limit: int = 100
    ) -> tuple[list[Company], int]:
        pattern = f"%{query}%"
        total = (
            self.db.scalar(
                select(func.count())
                .select_from(Company)
                .where(Company.name.ilike(pattern))
            )
            or 0
        )
        items = list(
            self.db.scalars(
                select(Company)
                .where(Company.name.ilike(pattern))
                .order_by(Company.name)
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total
