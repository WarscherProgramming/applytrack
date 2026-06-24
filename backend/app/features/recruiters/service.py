import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions.http import ConflictError, ValidationError
from app.features.companies.repository import CompanyRepository
from app.features.recruiters.model import Recruiter
from app.features.recruiters.repository import RecruiterRepository
from app.features.recruiters.schema import RecruiterCreate, RecruiterUpdate

logger = logging.getLogger(__name__)


class RecruiterService:
    def __init__(self, db: Session) -> None:
        self.repo = RecruiterRepository(db)
        # Validates company existence before insert/update — surfaces a clean
        # 404 instead of a PostgreSQL FK violation becoming a 500.
        self.company_repo = CompanyRepository(db)

    def create(self, data: RecruiterCreate) -> Recruiter:
        if data.company_id is not None:
            self.company_repo.get_or_raise(data.company_id)

        if data.email is not None:
            if self.repo.get_by_email(data.email):
                raise ConflictError("Recruiter", "email", data.email)

        recruiter = self.repo.create(data.model_dump())
        logger.info("Created recruiter id=%s email=%r", recruiter.id, recruiter.email)
        return recruiter

    def get(self, recruiter_id: UUID) -> Recruiter:
        return self.repo.get_or_raise(recruiter_id)

    def list(
        self,
        *,
        query: str | None = None,
        company_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Recruiter], int]:
        return self.repo.list_paginated(
            query=query,
            company_id=company_id,
            skip=skip,
            limit=limit,
        )

    def update(self, recruiter_id: UUID, data: RecruiterUpdate) -> Recruiter:
        recruiter = self.repo.get_or_raise(recruiter_id)
        updates = data.model_dump(exclude_unset=True)

        # Validate the new company only when company_id is being changed to a
        # non-null value. Sending null is a deliberate detach — always allowed.
        new_company_id = updates.get("company_id")
        if "company_id" in updates and new_company_id is not None:
            self.company_repo.get_or_raise(new_company_id)

        # Email uniqueness: skip when email is unchanged (avoids a spurious
        # conflict on a recruiter patching their own existing email).
        if "email" in updates:
            new_email = updates["email"]
            if new_email is not None and new_email != recruiter.email:
                if self.repo.get_by_email(new_email):
                    raise ConflictError("Recruiter", "email", new_email)

        # Cross-field invariant: merge the submitted patch with current values
        # before checking — the schema cannot validate this because it only sees
        # the submitted fields, not the full current state.
        merged_first = updates.get("first_name", recruiter.first_name)
        merged_last = updates.get("last_name", recruiter.last_name)
        merged_email = updates.get("email", recruiter.email)
        if not merged_first and not merged_last and not merged_email:
            raise ValidationError(
                "at least one of first_name, last_name, or email must be provided"
            )

        updated = self.repo.update(recruiter, updates)
        logger.info(
            "Updated recruiter id=%s fields=%s", recruiter_id, list(updates.keys())
        )
        return updated

    def delete(self, recruiter_id: UUID) -> None:
        recruiter = self.repo.get_or_raise(recruiter_id)
        self.repo.delete(recruiter)
        logger.info("Deleted recruiter id=%s", recruiter_id)
