from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel
from app.shared.ownership import UserOwnedMixin


class CalendarProvider(StrEnum):
    GOOGLE = "google"
    OUTLOOK = "outlook"
    ICS = "ics"


class CalendarConnectionStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class CalendarItemType(StrEnum):
    INTERVIEW = "interview"
    FOLLOW_UP = "follow_up"


class CalendarSyncStatus(StrEnum):
    SYNCED = "synced"
    DELETED = "deleted"
    ERROR = "error"


class CalendarConnection(UserOwnedMixin, BaseModel):
    __tablename__ = "calendar_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_calendar_connections_user_provider"),
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=CalendarConnectionStatus.DISCONNECTED.value
    )
    account_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    calendar_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class CalendarSyncEvent(UserOwnedMixin, BaseModel):
    __tablename__ = "calendar_sync_events"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider",
            "item_type",
            "item_id",
            name="uq_calendar_sync_user_provider_item",
        ),
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=CalendarSyncStatus.SYNCED.value,
        index=True,
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
