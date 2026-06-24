import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class Recruiter(BaseModel):
    __tablename__ = "recruiters"

    # Nullable FK — a recruiter may exist without a known company affiliation.
    # SET NULL keeps the contact record alive when its company is deleted;
    # RESTRICT would block company deletion, CASCADE would silently destroy contacts.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Uniqueness is enforced by a partial index in the migration (WHERE email IS NOT NULL).
    # Using a plain column unique=True would create a constraint that behaves
    # differently across databases; the partial index is explicit and portable.
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
