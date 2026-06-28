from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.core.security import validate_strong_password
from app.features.users.schemas import UserResponse
from app.shared.base_schema import AppBaseModel, EntitySchema


class ThemePreference(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class DashboardPagePreference(str, Enum):
    CAREER_COPILOT = "career_copilot"
    DASHBOARD = "dashboard"
    CAREER_INTELLIGENCE = "career_intelligence"
    DAILY_BRIEFING = "daily_briefing"
    TASKS = "tasks"


class NotificationBehavior(str, Enum):
    ALL = "all"
    IMPORTANT_ONLY = "important_only"
    MUTED = "muted"


class CalendarProviderPreference(str, Enum):
    NONE = "none"
    ICS = "ics"
    GOOGLE = "google"
    OUTLOOK = "outlook"


class AIProviderPreference(str, Enum):
    AUTO = "auto"
    MOCK = "mock"
    OPENAI = "openai"


class NotificationPreferences(AppBaseModel):
    follow_up_reminders: bool = True
    interview_reminders: bool = True
    gmail_activity: bool = True
    opportunity_alerts: bool = True
    ai_insight_alerts: bool = True


class SettingsResponse(EntitySchema):
    user_id: UUID
    timezone: str
    notification_preferences: NotificationPreferences
    theme: ThemePreference
    default_dashboard_page: DashboardPagePreference
    default_notification_behavior: NotificationBehavior
    preferred_calendar_provider: CalendarProviderPreference
    preferred_ai_provider: AIProviderPreference


class SettingsCenterResponse(AppBaseModel):
    account: UserResponse
    settings: SettingsResponse
    available_ai_providers: list[str]


class AccountSettingsUpdate(AppBaseModel):
    full_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    timezone: str | None = Field(None, min_length=1, max_length=64)
    notification_preferences: NotificationPreferences | None = None


class PreferencesUpdate(AppBaseModel):
    theme: ThemePreference | None = None
    default_dashboard_page: DashboardPagePreference | None = None
    default_notification_behavior: NotificationBehavior | None = None
    preferred_calendar_provider: CalendarProviderPreference | None = None
    preferred_ai_provider: AIProviderPreference | None = None


class NotificationSettingsUpdate(AppBaseModel):
    notification_preferences: NotificationPreferences | None = None
    default_notification_behavior: NotificationBehavior | None = None


class PasswordChangeRequest(AppBaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    current_refresh_token: str | None = Field(None, min_length=20)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)


class PasswordChangeResponse(AppBaseModel):
    password_changed: bool
    old_refresh_tokens_invalidated: bool


class SessionTokenRequest(AppBaseModel):
    refresh_token: str = Field(..., min_length=20)


class SessionResponse(AppBaseModel):
    id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    is_current: bool = False
    is_active: bool


class SessionListResponse(AppBaseModel):
    items: list[SessionResponse]
    active_count: int


class SessionActionResponse(AppBaseModel):
    signed_out: bool
    revoked_count: int


class DataExportResponse(AppBaseModel):
    exported_at: datetime
    user: UserResponse
    data: dict[str, list[dict]]
