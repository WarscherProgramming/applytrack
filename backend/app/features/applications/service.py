import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.applications.repository import ApplicationRepository
from app.features.applications.schema import ApplicationCreate, ApplicationUpdate
from app.features.companies.repository import CompanyRepository
from app.features.cover_letters.repository import CoverLetterRepository
from app.features.resumes.repository import ResumeRepository

logger = logging.getLogger(__name__)


class ApplicationService:
    def __init__(self, db: Session, user_id: UUID) -> None:
        self.user_id = user_id
        self.repo = ApplicationRepository(db)
        # Used to validate company existence before inserting — yields a clean
        # 404 rather than a PostgreSQL FK violation surfacing as a 500.
        self.company_repo = CompanyRepository(db)
        # Validate the optional submitted-document references the same way.
        self.resume_repo = ResumeRepository(db)
        self.cover_letter_repo = CoverLetterRepository(db)

    def create(self, data: ApplicationCreate) -> JobApplication:
        self.company_repo.get_or_raise_for_user(data.company_id, self.user_id)
        if data.resume_id is not None:
            self.resume_repo.get_or_raise_for_user(data.resume_id, self.user_id)
        if data.cover_letter_id is not None:
            self.cover_letter_repo.get_or_raise_for_user(data.cover_letter_id, self.user_id)
        application = self.repo.create(data.model_dump() | {"user_id": self.user_id})
        logger.info(
            "Created application id=%s company_id=%s job_title=%r",
            application.id,
            application.company_id,
            application.job_title,
        )
        return application

    def get(self, application_id: UUID) -> JobApplication:
        return self.repo.get_or_raise_for_user(application_id, self.user_id)

    def list(
        self,
        *,
        query: str | None = None,
        status: ApplicationStatus | None = None,
        company_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[JobApplication], int]:
        return self.repo.list_paginated(
            query=query,
            status=status,
            company_id=company_id,
            user_id=self.user_id,
            skip=skip,
            limit=limit,
        )

    def update(self, application_id: UUID, data: ApplicationUpdate) -> JobApplication:
        application = self.repo.get_or_raise_for_user(application_id, self.user_id)
        updates = data.model_dump(exclude_unset=True)

        new_company_id = updates.get("company_id")
        if new_company_id is not None:
            self.company_repo.get_or_raise_for_user(new_company_id, self.user_id)
        # Validate any FK target being set to a non-null value. Sending null is
        # an explicit detach (clear the submitted document) and is always allowed.
        if updates.get("resume_id") is not None:
            self.resume_repo.get_or_raise_for_user(updates["resume_id"], self.user_id)
        if updates.get("cover_letter_id") is not None:
            self.cover_letter_repo.get_or_raise_for_user(
                updates["cover_letter_id"],
                self.user_id,
            )

        updated = self.repo.update(application, updates)
        logger.info(
            "Updated application id=%s fields=%s",
            application_id,
            list(updates.keys()),
        )
        return updated

    def delete(self, application_id: UUID) -> None:
        application = self.repo.get_or_raise_for_user(application_id, self.user_id)
        self.repo.delete(application)
        logger.info("Deleted application id=%s", application_id)
