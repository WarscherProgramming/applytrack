from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.features.followups.model import (
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)
from app.shared.base_schema import AppBaseModel, EntitySchema


class FollowUpBase(AppBaseModel):
    application_id: UUID
    recruiter_id: UUID | None = None
    interview_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    # Required — every follow-up has a type; CUSTOM is the escape hatch when
    # none of the specific categories fit, so there is no sensible default.
    followup_type: FollowUpType
    status: FollowUpStatus = FollowUpStatus.PENDING
    priority: FollowUpPriority = FollowUpPriority.MEDIUM
    due_date: date
    # Client may set this explicitly, but the service auto-manages it on most
    # status transitions (see FollowUpService.update / .create).
    completed_at: datetime | None = None


class FollowUpCreate(FollowUpBase):
    pass


class FollowUpUpdate(AppBaseModel):
    """PATCH schema — every field is optional; only submitted fields are written.

    The service uses model_dump(exclude_unset=True) so omitting a field leaves
    its current value untouched, while sending null explicitly clears a
    nullable field.
    """

    application_id: UUID | None = None
    recruiter_id: UUID | None = None
    interview_id: UUID | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    followup_type: FollowUpType | None = None
    status: FollowUpStatus | None = None
    priority: FollowUpPriority | None = None
    due_date: date | None = None
    completed_at: datetime | None = None


class FollowUpResponse(EntitySchema):
    application_id: UUID
    recruiter_id: UUID | None
    interview_id: UUID | None
    title: str
    description: str | None
    followup_type: FollowUpType
    status: FollowUpStatus
    priority: FollowUpPriority
    due_date: date
    completed_at: datetime | None


class FollowUpListResponse(AppBaseModel):
    items: list[FollowUpResponse]
    total: int
    skip: int
    limit: int
