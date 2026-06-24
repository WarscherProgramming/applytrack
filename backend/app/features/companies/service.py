import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions.http import ConflictError
from app.features.companies.model import Company
from app.features.companies.repository import CompanyRepository
from app.features.companies.schema import CompanyCreate, CompanyUpdate

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, db: Session) -> None:
        self.repo = CompanyRepository(db)

    def create(self, data: CompanyCreate) -> Company:
        if self.repo.get_by_name(data.name):
            raise ConflictError("Company", "name", data.name)
        company = self.repo.create(data.model_dump())
        logger.info("Created company name=%r id=%s", company.name, company.id)
        return company

    def get(self, company_id: UUID) -> Company:
        return self.repo.get_or_raise(company_id)

    def list(
        self,
        *,
        query: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Company], int]:
        if query:
            return self.repo.search(query, skip=skip, limit=limit)
        return self.repo.get_all_paginated(skip=skip, limit=limit)

    def update(self, company_id: UUID, data: CompanyUpdate) -> Company:
        company = self.repo.get_or_raise(company_id)
        updates = data.model_dump(exclude_unset=True)

        # Only check for a name conflict when the name is actually changing.
        # Updating a company with its own current name must not raise ConflictError.
        new_name = updates.get("name")
        if new_name is not None and new_name != company.name:
            if self.repo.get_by_name(new_name):
                raise ConflictError("Company", "name", new_name)

        updated = self.repo.update(company, updates)
        logger.info("Updated company id=%s fields=%s", company_id, list(updates.keys()))
        return updated

    def delete(self, company_id: UUID) -> None:
        company = self.repo.get_or_raise(company_id)
        self.repo.delete(company)
        logger.info("Deleted company id=%s name=%r", company_id, company.name)
