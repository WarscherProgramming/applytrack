import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel
from app.shared.ownership import UserOwnedMixin


class GmailAccount(UserOwnedMixin, BaseModel):
    """A connected Gmail account. Single-account today, but modelled as a table
    so multi-account/multi-user is a non-breaking change later."""

    __tablename__ = "gmail_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "email_address", name="uq_gmail_accounts_user_email"),
    )

    email_address: Mapped[str] = mapped_column(
        String(320), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="connected"
    )
    # Tokens are stored Fernet-encrypted (see token_crypto). Never plaintext.
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_status: Mapped[str | None] = mapped_column(String(50), nullable=True)


class EmailMessage(UserOwnedMixin, BaseModel):
    """An imported Gmail message with its automatic match results."""

    __tablename__ = "email_messages"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gmail_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Gmail identifiers.
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipients: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 'inbound' (Inbox) or 'outbound' (Sent).
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    labels: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Automatic match results (all nullable; SET NULL so deleting a linked
    # entity never destroys the imported email).
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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
    match_confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    match_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
