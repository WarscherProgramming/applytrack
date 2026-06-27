from enum import StrEnum

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class NotificationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationCategory(StrEnum):
    FOLLOW_UP = "follow_up"
    INTERVIEW = "interview"
    GMAIL = "gmail"
    OPPORTUNITY = "opportunity"
    AI_INSIGHT = "ai_insight"


class Notification(BaseModel):
    __tablename__ = "notifications"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
