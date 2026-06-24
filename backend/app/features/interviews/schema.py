from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.features.interviews.model import InterviewStatus, InterviewType
from app.shared.base_schema import AppBaseModel, EntitySchema


class InterviewBase(AppBaseModel):
    application_id: UUID
    recruiter_id: UUID | None = None
    interview_type: InterviewType | None = None
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=480)
    location: str | None = Field(None, max_length=255)
    meeting_link: str | None = Field(None, max_length=2000)
    status: InterviewStatus = InterviewStatus.SCHEDULED
    notes: str | None = None
    feedback: str | None = None


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(AppBaseModel):
    """PATCH schema — every field is optional; only submitted fields are written.

    The service uses model_dump(exclude_unset=True) so omitting a field leaves
    the current value unchanged. Sending null for a nullable field clears it.
    """

    application_id: UUID | None = None
    recruiter_id: UUID | None = None
    interview_type: InterviewType | None = None
    scheduled_at: datetime | None = None
    # ge/le constraints apply when the value is a non-null int.
    duration_minutes: int | None = Field(None, ge=15, le=480)
    location: str | None = Field(None, max_length=255)
    meeting_link: str | None = Field(None, max_length=2000)
    status: InterviewStatus | None = None
    notes: str | None = None
    feedback: str | None = None


class InterviewResponse(EntitySchema):
    application_id: UUID
    recruiter_id: UUID | None
    interview_type: InterviewType | None
    scheduled_at: datetime
    duration_minutes: int
    location: str | None
    meeting_link: str | None
    status: InterviewStatus
    notes: str | None
    feedback: str | None


class InterviewListResponse(AppBaseModel):
    items: list[InterviewResponse]
    total: int
    skip: int
    limit: int
