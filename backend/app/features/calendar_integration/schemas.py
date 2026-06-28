from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.features.calendar_integration.model import (
    CalendarConnectionStatus,
    CalendarItemType,
    CalendarProvider,
    CalendarSyncStatus,
)
from app.shared.base_schema import AppBaseModel, EntitySchema


class CalendarEventPayload(AppBaseModel):
    item_type: CalendarItemType
    item_id: str
    title: str
    description: str | None = None
    location: str | None = None
    start_at: datetime
    end_at: datetime
    status: str
    source_updated_at: datetime


class CalendarConnectionResponse(AppBaseModel):
    provider: CalendarProvider
    status: CalendarConnectionStatus
    account_email: str | None
    calendar_id: str | None
    last_sync_at: datetime | None
    last_sync_status: str | None
    last_error: str | None


class CalendarStatusResponse(AppBaseModel):
    connections: list[CalendarConnectionResponse]
    synced_event_count: int
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    last_error: str | None = None


class CalendarConnectResponse(AppBaseModel):
    provider: CalendarProvider
    authorization_url: str | None = None
    connected: bool
    message: str


class CalendarSyncEventResponse(EntitySchema):
    provider: CalendarProvider
    item_type: CalendarItemType
    item_id: str
    external_event_id: str
    event_hash: str
    status: CalendarSyncStatus
    last_synced_at: datetime | None
    last_error: str | None


class CalendarSyncSummary(AppBaseModel):
    provider: CalendarProvider
    created: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0
    errors: list[str] = Field(default_factory=list)
    synced_event_count: int = 0
    last_sync_at: datetime


class ManualSyncRequest(AppBaseModel):
    provider: CalendarProvider = CalendarProvider.GOOGLE
    include_interviews: bool = True
    include_followups: bool = True


class SyncItemRequest(AppBaseModel):
    provider: CalendarProvider = CalendarProvider.GOOGLE


class CalendarDisconnectResponse(AppBaseModel):
    provider: CalendarProvider
    disconnected: bool


class CalendarCallbackResponse(AppBaseModel):
    provider: CalendarProvider
    connected: bool
    message: str


class SyncedItemStatus(AppBaseModel):
    provider: CalendarProvider
    item_type: CalendarItemType
    item_id: UUID
    sync_event: CalendarSyncEventResponse | None = None
