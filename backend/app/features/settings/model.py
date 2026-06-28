import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class UserSettings(BaseModel):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    notification_preferences: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    theme: Mapped[str] = mapped_column(String(20), nullable=False, default="system")
    default_dashboard_page: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="career_copilot",
    )
    default_notification_behavior: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="all",
    )
    preferred_calendar_provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="ics",
    )
    preferred_ai_provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="auto",
    )
