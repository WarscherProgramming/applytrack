from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.calendar_integration.model import CalendarProvider
from app.features.calendar_integration.schemas import (
    CalendarCallbackResponse,
    CalendarConnectResponse,
    CalendarDisconnectResponse,
    CalendarStatusResponse,
    CalendarSyncSummary,
    ManualSyncRequest,
    SyncItemRequest,
)
from app.features.calendar_integration.service import CalendarIntegrationService

router = APIRouter(prefix="/calendar-integration", tags=["calendar_integration"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> CalendarIntegrationService:
    return CalendarIntegrationService(db)


ServiceDep = Annotated[CalendarIntegrationService, Depends(_get_service)]


@router.get("/status", response_model=CalendarStatusResponse)
def get_calendar_status(service: ServiceDep) -> CalendarStatusResponse:
    return service.status()


@router.post("/connect/{provider}", response_model=CalendarConnectResponse)
def connect_calendar(
    provider: CalendarProvider, service: ServiceDep
) -> CalendarConnectResponse:
    return service.connect(provider)


@router.get("/{provider}/callback", response_model=CalendarCallbackResponse)
def calendar_oauth_callback(
    provider: CalendarProvider,
    service: ServiceDep,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
) -> CalendarCallbackResponse:
    return service.complete_oauth(provider, code=code, state=state)


@router.post("/disconnect/{provider}", response_model=CalendarDisconnectResponse)
def disconnect_calendar(
    provider: CalendarProvider, service: ServiceDep
) -> CalendarDisconnectResponse:
    return service.disconnect(provider)


@router.post("/sync", response_model=CalendarSyncSummary)
def sync_calendar(
    data: ManualSyncRequest, service: ServiceDep
) -> CalendarSyncSummary:
    return service.sync(data)


@router.post("/interviews/{interview_id}/sync", response_model=CalendarSyncSummary)
def sync_interview_to_calendar(
    interview_id: UUID, data: SyncItemRequest, service: ServiceDep
) -> CalendarSyncSummary:
    return service.sync_interview(interview_id, data)


@router.post("/followups/{followup_id}/sync", response_model=CalendarSyncSummary)
def sync_followup_to_calendar(
    followup_id: UUID, data: SyncItemRequest, service: ServiceDep
) -> CalendarSyncSummary:
    return service.sync_followup(followup_id, data)


@router.get("/ics", response_class=Response)
def export_calendar_ics(service: ServiceDep) -> Response:
    return Response(
        content=service.ics_export(),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="applytrack-calendar.ics"'},
    )
