from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.settings.schemas import (
    AccountSettingsUpdate,
    DataExportResponse,
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
from app.features.settings.service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> SettingsService:
    return SettingsService(db)


ServiceDep = Annotated[SettingsService, Depends(_get_service)]


@router.get("/", response_model=SettingsCenterResponse)
def get_settings(user: CurrentUser, service: ServiceDep) -> SettingsCenterResponse:
    return service.get_settings_center(user)


@router.patch("/account", response_model=SettingsCenterResponse)
def update_account(
    data: AccountSettingsUpdate,
    user: CurrentUser,
    service: ServiceDep,
) -> SettingsCenterResponse:
    return service.update_account(user, data)


@router.patch("/preferences", response_model=SettingsResponse)
def update_preferences(
    data: PreferencesUpdate,
    user: CurrentUser,
    service: ServiceDep,
) -> SettingsResponse:
    return service.update_preferences(user, data)


@router.patch("/notifications", response_model=SettingsResponse)
def update_notifications(
    data: NotificationSettingsUpdate,
    user: CurrentUser,
    service: ServiceDep,
) -> SettingsResponse:
    return service.update_notifications(user, data)


@router.post("/security/change-password", response_model=PasswordChangeResponse)
def change_password(
    data: PasswordChangeRequest,
    user: CurrentUser,
    service: ServiceDep,
) -> PasswordChangeResponse:
    return service.change_password(user, data)


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(user: CurrentUser, service: ServiceDep) -> SessionListResponse:
    return service.list_sessions(user)


@router.post("/sessions", response_model=SessionListResponse)
def list_sessions_with_current(
    data: SessionTokenRequest,
    user: CurrentUser,
    service: ServiceDep,
) -> SessionListResponse:
    return service.list_sessions(user, data)


@router.post("/sessions/current", response_model=SessionResponse)
def current_session(
    data: SessionTokenRequest,
    user: CurrentUser,
    service: ServiceDep,
) -> SessionResponse:
    return service.current_session(user, data)


@router.post("/sessions/logout-current", response_model=SessionActionResponse)
def sign_out_current(
    data: SessionTokenRequest,
    user: CurrentUser,
    service: ServiceDep,
) -> SessionActionResponse:
    return service.sign_out_current(user, data)


@router.post("/sessions/logout-all", response_model=SessionActionResponse)
def sign_out_all(user: CurrentUser, service: ServiceDep) -> SessionActionResponse:
    return service.sign_out_all(user)


@router.get("/export", response_model=DataExportResponse)
def export_data(user: CurrentUser, service: ServiceDep) -> DataExportResponse:
    return service.export_data(user)
