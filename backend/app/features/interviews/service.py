import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.features.applications.repository import ApplicationRepository
from app.features.interviews.model import Interview, InterviewStatus, InterviewType
from app.features.interviews.repository import InterviewRepository
from app.features.interviews.schema import InterviewCreate, InterviewUpdate
from app.features.recruiters.repository import RecruiterRepository

logger = logging.getLogger(__name__)


class InterviewService:
    def __init__(self, db: Session, user_id: UUID) -> None:
        self.user_id = user_id
        self.repo = InterviewRepository(db)
        # Both cross-feature repos are injected here to produce clean 404s
        # rather than letting FK violations surface as opaque 500 errors.
        self.application_repo = ApplicationRepository(db)
        self.recruiter_repo = RecruiterRepository(db)

    def create(self, data: InterviewCreate) -> Interview:
        self.application_repo.get_or_raise_for_user(data.application_id, self.user_id)

        if data.recruiter_id is not None:
            self.recruiter_repo.get_or_raise_for_user(data.recruiter_id, self.user_id)

        interview = self.repo.create(data.model_dump() | {"user_id": self.user_id})
        logger.info(
            "Created interview id=%s application_id=%s",
            interview.id,
            interview.application_id,
        )
        return interview

    def get(self, interview_id: UUID) -> Interview:
        return self.repo.get_or_raise_for_user(interview_id, self.user_id)

    def list(
        self,
        *,
        application_id: UUID | None = None,
        recruiter_id: UUID | None = None,
        status: InterviewStatus | None = None,
        interview_type: InterviewType | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Interview], int]:
        return self.repo.list_paginated(
            application_id=application_id,
            recruiter_id=recruiter_id,
            status=status,
            interview_type=interview_type,
            user_id=self.user_id,
            skip=skip,
            limit=limit,
        )

    def update(self, interview_id: UUID, data: InterviewUpdate) -> Interview:
        interview = self.repo.get_or_raise_for_user(interview_id, self.user_id)
        updates = data.model_dump(exclude_unset=True)

        # Validate the new application if application_id is being changed.
        new_application_id = updates.get("application_id")
        if "application_id" in updates and new_application_id is not None:
            self.application_repo.get_or_raise_for_user(new_application_id, self.user_id)

        # Validate the new recruiter only when setting a non-null value.
        # Sending null is an explicit detach — always permitted.
        new_recruiter_id = updates.get("recruiter_id")
        if "recruiter_id" in updates and new_recruiter_id is not None:
            self.recruiter_repo.get_or_raise_for_user(new_recruiter_id, self.user_id)

        updated = self.repo.update(interview, updates)
        logger.info(
            "Updated interview id=%s fields=%s",
            interview_id,
            list(updates.keys()),
        )
        return updated

    def delete(self, interview_id: UUID) -> None:
        interview = self.repo.get_or_raise_for_user(interview_id, self.user_id)
        self.repo.delete(interview)
        logger.info("Deleted interview id=%s", interview_id)
