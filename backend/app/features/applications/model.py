import enum
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel
from app.shared.ownership import UserOwnedMixin


class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    ASSESSMENT = "assessment"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    FINAL_INTERVIEW = "final_interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    GHOSTED = "ghosted"


class JobApplication(UserOwnedMixin, BaseModel):
    __tablename__ = "job_applications"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    job_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    job_link: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Status is stored as a plain string; the enum constraint lives in Pydantic,
    # not in the DB, so adding new statuses never requires ALTER TYPE.
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ApplicationStatus.DRAFT.value,
        index=True,
    )
    date_applied: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional references to the exact resume / cover-letter version submitted
    # with this application. SET NULL keeps the application intact if the
    # referenced document is later deleted — losing the link must never delete
    # the application record.
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cover_letter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cover_letters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
