import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel
from app.shared.ownership import UserOwnedMixin


class FollowUpType(str, enum.Enum):
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    LINKEDIN = "linkedin"
    THANK_YOU = "thank_you"
    RECRUITER_CHECKIN = "recruiter_checkin"
    INTERVIEW_FOLLOWUP = "interview_followup"
    APPLICATION_CHECKIN = "application_checkin"
    CUSTOM = "custom"


class FollowUpStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class FollowUpPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FollowUp(UserOwnedMixin, BaseModel):
    __tablename__ = "followups"

    # Required FK — a follow-up always tracks work for a specific application.
    # CASCADE: deleting an application removes its follow-ups (they have no
    # meaning without the application).
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Optional FKs — a follow-up may reference the recruiter and/or interview
    # it relates to. SET NULL keeps the follow-up alive when either is deleted;
    # the reminder itself remains actionable.
    recruiter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recruiters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    interview_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Text (unbounded in DB); the 5000-char cap is enforced in Pydantic so the
    # limit can change without a migration.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Enums stored as plain strings; constraint lives in Pydantic so adding new
    # values never requires ALTER TYPE on a production table.
    followup_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FollowUpStatus.PENDING.value,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FollowUpPriority.MEDIUM.value,
        index=True,
    )

    # Date (calendar day) not DateTime — "due today / this week / overdue" are
    # calendar questions. May be in the past to support overdue reminders.
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # Timestamp, auto-managed by the service on status transitions.
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
