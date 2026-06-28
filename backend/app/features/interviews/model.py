import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel
from app.shared.ownership import UserOwnedMixin


class InterviewType(str, enum.Enum):
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    ONSITE = "onsite"
    FINAL = "final"
    RECRUITER_CALL = "recruiter_call"
    HIRING_MANAGER = "hiring_manager"
    OTHER = "other"


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


class Interview(UserOwnedMixin, BaseModel):
    __tablename__ = "interviews"

    # Required FK — an interview without an application is meaningless.
    # CASCADE: deleting an application removes its interviews automatically.
    # RESTRICT would force users to delete interviews before applications.
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional FK — the linked recruiter may be unknown or may be deleted later.
    # SET NULL keeps the interview record intact when a recruiter is removed.
    recruiter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recruiters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Stored as plain string; enum constraint lives in Pydantic so adding new
    # types never requires ALTER TYPE on a production table.
    interview_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=InterviewStatus.SCHEDULED.value,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
