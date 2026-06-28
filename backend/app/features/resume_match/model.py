import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel
from app.shared.ownership import UserOwnedMixin


class ResumeMatchAnalysis(UserOwnedMixin, BaseModel):
    """
    A stored Resume Match analysis (history record).

    One row per analysis run. The full structured AI output is kept in `result`
    (JSONB) so the exact analysis can be reopened later, while overall_match_score
    is denormalised into its own column for cheap list ordering/filtering.
    """

    __tablename__ = "resume_match_analyses"

    # SET NULL: history survives even if the resume is later deleted. resume_name
    # snapshots the resume's name+version at analysis time so the record stays
    # readable regardless of the FK's fate.
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_name: Mapped[str] = mapped_column(String(255), nullable=False)

    job_description: Mapped[str] = mapped_column(Text, nullable=False)

    overall_match_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Full ResumeMatchResult payload (strengths, weaknesses, etc.).
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Which provider/model produced the analysis, for transparency in history.
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
