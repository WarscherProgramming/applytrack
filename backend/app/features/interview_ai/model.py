import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel
from app.shared.ownership import UserOwnedMixin


class InterviewPrepPackage(UserOwnedMixin, BaseModel):
    """
    A stored interview-preparation package (history record).

    Every generation is saved so packages can be reopened and compared. The full
    structured output lives in `result` (JSONB); context snapshots (company,
    title, type, round) and usage are denormalised for list display and history
    transparency. FKs are SET NULL so history survives if the application/resume
    is later deleted.
    """

    __tablename__ = "interview_prep_packages"

    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    interview_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    interview_round: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)

    result: Mapped[dict] = mapped_column(JSONB, nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 6), nullable=True
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
