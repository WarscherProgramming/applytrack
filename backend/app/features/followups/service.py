import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.features.applications.repository import ApplicationRepository
from app.features.followups.model import (
    FollowUp,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)
from app.features.followups.repository import FollowUpRepository
from app.features.followups.schema import FollowUpCreate, FollowUpUpdate
from app.features.interviews.repository import InterviewRepository
from app.features.recruiters.repository import RecruiterRepository

logger = logging.getLogger(__name__)


class FollowUpService:
    def __init__(self, db: Session) -> None:
        self.repo = FollowUpRepository(db)
        # All three cross-feature repos are injected to validate FK targets
        # before insert/update — yielding clean 404s instead of letting a
        # PostgreSQL FK violation surface as an opaque 500.
        self.application_repo = ApplicationRepository(db)
        self.recruiter_repo = RecruiterRepository(db)
        self.interview_repo = InterviewRepository(db)

    def create(self, data: FollowUpCreate) -> FollowUp:
        self.application_repo.get_or_raise(data.application_id)
        if data.recruiter_id is not None:
            self.recruiter_repo.get_or_raise(data.recruiter_id)
        if data.interview_id is not None:
            self.interview_repo.get_or_raise(data.interview_id)

        payload = data.model_dump()
        # A follow-up created already-completed gets a completed_at stamp so it
        # never lands in the inconsistent "completed but never timestamped"
        # state. Mirrors the transition logic in update().
        if (
            payload.get("status") == FollowUpStatus.COMPLETED
            and payload.get("completed_at") is None
        ):
            payload["completed_at"] = datetime.now(timezone.utc)

        followup = self.repo.create(payload)
        logger.info(
            "Created followup id=%s application_id=%s status=%s",
            followup.id,
            followup.application_id,
            followup.status,
        )
        return followup

    def get(self, followup_id: UUID) -> FollowUp:
        return self.repo.get_or_raise(followup_id)

    def list(
        self,
        *,
        application_id: UUID | None = None,
        recruiter_id: UUID | None = None,
        interview_id: UUID | None = None,
        status: FollowUpStatus | None = None,
        priority: FollowUpPriority | None = None,
        followup_type: FollowUpType | None = None,
        overdue: bool = False,
        due_today: bool = False,
        due_this_week: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[FollowUp], int]:
        return self.repo.list_paginated(
            application_id=application_id,
            recruiter_id=recruiter_id,
            interview_id=interview_id,
            status=status,
            priority=priority,
            followup_type=followup_type,
            overdue=overdue,
            due_today=due_today,
            due_this_week=due_this_week,
            skip=skip,
            limit=limit,
        )

    def update(self, followup_id: UUID, data: FollowUpUpdate) -> FollowUp:
        followup = self.repo.get_or_raise(followup_id)
        updates = data.model_dump(exclude_unset=True)

        # Validate any FK target that is being changed to a non-null value.
        # Sending null for an optional FK is an explicit detach — always allowed.
        new_application_id = updates.get("application_id")
        if "application_id" in updates and new_application_id is not None:
            self.application_repo.get_or_raise(new_application_id)
        new_recruiter_id = updates.get("recruiter_id")
        if "recruiter_id" in updates and new_recruiter_id is not None:
            self.recruiter_repo.get_or_raise(new_recruiter_id)
        new_interview_id = updates.get("interview_id")
        if "interview_id" in updates and new_interview_id is not None:
            self.interview_repo.get_or_raise(new_interview_id)

        # Automatic completed_at management on status transitions.
        # The "completed_at" not in updates guard means an explicit client-sent
        # value always wins over the automatic behaviour.
        if "status" in updates:
            new_status = updates["status"]
            if new_status == FollowUpStatus.COMPLETED:
                if "completed_at" not in updates and followup.completed_at is None:
                    updates["completed_at"] = datetime.now(timezone.utc)
            elif new_status == FollowUpStatus.PENDING:
                # Reopening a follow-up clears its completion timestamp.
                if "completed_at" not in updates:
                    updates["completed_at"] = None

        updated = self.repo.update(followup, updates)
        logger.info(
            "Updated followup id=%s fields=%s",
            followup_id,
            list(updates.keys()),
        )
        return updated

    def delete(self, followup_id: UUID) -> None:
        followup = self.repo.get_or_raise(followup_id)
        self.repo.delete(followup)
        logger.info("Deleted followup id=%s", followup_id)
