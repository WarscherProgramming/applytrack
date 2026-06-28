from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.security import hash_password, hash_token, verify_password
from app.exceptions.http import NotFoundError, UnauthorizedError, ValidationError
from app.features.settings.model import UserSettings
from app.features.settings.repository import SettingsRepository
from app.features.settings.schemas import (
    AccountSettingsUpdate,
    AIProviderPreference,
    DataExportResponse,
    NotificationPreferences,
    NotificationSettingsUpdate,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PreferencesUpdate,
    SessionActionResponse,
    SessionListResponse,
    SessionResponse,
    SessionTokenRequest,
    SettingsCenterResponse,
    SettingsResponse,
)
from app.features.users.model import User
from app.features.users.schemas import UserResponse, UserUpdate
from app.features.users.service import UserService


class SettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SettingsRepository(db)
        self.user_service = UserService(db)

    def get_settings_center(self, user: User) -> SettingsCenterResponse:
        settings = self.repo.get_or_create_for_user(user)
        return SettingsCenterResponse(
            account=UserResponse.model_validate(user),
            settings=_settings_response(settings),
            available_ai_providers=self.available_ai_providers(),
        )

    def update_account(self, user: User, data: AccountSettingsUpdate) -> SettingsCenterResponse:
        settings = self.repo.get_or_create_for_user(user)
        user_updates = {}
        if "email" in data.model_fields_set and data.email is not None:
            user_updates["email"] = data.email
        if "full_name" in data.model_fields_set:
            user_updates["full_name"] = data.full_name
        updated_user = (
            self.user_service.update_me(user, UserUpdate(**user_updates))
            if user_updates
            else user
        )
        updates: dict = {}
        if data.timezone is not None:
            updates["timezone"] = data.timezone
        if data.notification_preferences is not None:
            updates["notification_preferences"] = data.notification_preferences.model_dump()
        if updates:
            settings = self.repo.update(settings, updates)
        return SettingsCenterResponse(
            account=UserResponse.model_validate(updated_user),
            settings=_settings_response(settings),
            available_ai_providers=self.available_ai_providers(),
        )

    def update_preferences(self, user: User, data: PreferencesUpdate) -> SettingsResponse:
        settings = self.repo.get_or_create_for_user(user)
        updates = data.model_dump(exclude_unset=True)
        preferred_ai_provider = updates.get("preferred_ai_provider")
        if preferred_ai_provider is not None:
            self._validate_ai_provider(preferred_ai_provider)
        return _settings_response(self.repo.update(settings, _enum_values(updates)))

    def update_notifications(
        self, user: User, data: NotificationSettingsUpdate
    ) -> SettingsResponse:
        settings = self.repo.get_or_create_for_user(user)
        updates = data.model_dump(exclude_unset=True)
        if data.notification_preferences is not None:
            updates["notification_preferences"] = data.notification_preferences.model_dump()
        return _settings_response(self.repo.update(settings, _enum_values(updates)))

    def change_password(
        self, user: User, data: PasswordChangeRequest
    ) -> PasswordChangeResponse:
        if not verify_password(data.current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")
        user.hashed_password = hash_password(data.new_password)
        current_hash = hash_token(data.current_refresh_token) if data.current_refresh_token else None
        revoked = self.repo.revoke_old_sessions(user, current_hash)
        self.db.flush()
        return PasswordChangeResponse(
            password_changed=True,
            old_refresh_tokens_invalidated=revoked > 0,
        )

    def list_sessions(
        self, user: User, data: SessionTokenRequest | None = None
    ) -> SessionListResponse:
        current_hash = hash_token(data.refresh_token) if data else None
        sessions = [
            _session_response(token, is_current=token.token_hash == current_hash)
            for token in self.repo.list_sessions(user)
        ]
        return SessionListResponse(
            items=sessions,
            active_count=sum(1 for item in sessions if item.is_active),
        )

    def current_session(self, user: User, data: SessionTokenRequest) -> SessionResponse:
        token = self.repo.get_session_by_hash(user, hash_token(data.refresh_token))
        if token is None:
            raise NotFoundError("RefreshToken", UUID(int=0))
        return _session_response(token, is_current=True)

    def sign_out_current(self, user: User, data: SessionTokenRequest) -> SessionActionResponse:
        token = self.repo.get_session_by_hash(user, hash_token(data.refresh_token))
        if token is None:
            raise NotFoundError("RefreshToken", UUID(int=0))
        was_active = _is_active(token)
        if token.revoked_at is None:
            self.repo.revoke_session(token)
        return SessionActionResponse(signed_out=True, revoked_count=1 if was_active else 0)

    def sign_out_all(self, user: User) -> SessionActionResponse:
        revoked = self.repo.revoke_all_sessions(user)
        return SessionActionResponse(signed_out=True, revoked_count=revoked)

    def export_data(self, user: User) -> DataExportResponse:
        return DataExportResponse(
            exported_at=datetime.now(UTC),
            user=UserResponse.model_validate(user),
            data=self.repo.export_data(user),
        )

    def available_ai_providers(self) -> list[str]:
        providers = ["mock"]
        if app_settings.ai_configured:
            providers.append("openai")
        return providers

    def _validate_ai_provider(self, provider: AIProviderPreference | str) -> None:
        value = provider.value if isinstance(provider, AIProviderPreference) else provider
        if value == AIProviderPreference.AUTO.value:
            return
        if value not in self.available_ai_providers():
            raise ValidationError(f"AI provider '{value}' is not configured")


def _settings_response(settings: UserSettings) -> SettingsResponse:
    return SettingsResponse(
        id=settings.id,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
        user_id=settings.user_id,
        timezone=settings.timezone,
        notification_preferences=NotificationPreferences.model_validate(
            settings.notification_preferences or {}
        ),
        theme=settings.theme,
        default_dashboard_page=settings.default_dashboard_page,
        default_notification_behavior=settings.default_notification_behavior,
        preferred_calendar_provider=settings.preferred_calendar_provider,
        preferred_ai_provider=settings.preferred_ai_provider,
    )


def _session_response(token, *, is_current: bool) -> SessionResponse:
    return SessionResponse(
        id=token.id,
        created_at=token.created_at,
        expires_at=token.expires_at,
        revoked_at=token.revoked_at,
        is_current=is_current,
        is_active=_is_active(token),
    )


def _is_active(token) -> bool:
    return token.revoked_at is None and token.expires_at > datetime.now(UTC)


def _enum_values(data: dict) -> dict:
    return {
        key: value.value if hasattr(value, "value") else value
        for key, value in data.items()
    }
