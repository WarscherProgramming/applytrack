from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.gmail.schemas import (
    EmailListResponse,
    GmailConnectResponse,
    GmailStatusResponse,
    GmailSyncResponse,
    TimelineEvent,
    TimelineResponse,
)
from app.features.gmail.service import GmailService

router = APIRouter(prefix="/gmail", tags=["gmail"])


def _get_service(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
) -> GmailService:
    return GmailService(db, user.id)


ServiceDep = Annotated[GmailService, Depends(_get_service)]


@router.get("/status", response_model=GmailStatusResponse)
def gmail_status(service: ServiceDep) -> GmailStatusResponse:
    return GmailStatusResponse(**service.get_status())


@router.post("/connect", response_model=GmailConnectResponse)
def gmail_connect(service: ServiceDep) -> GmailConnectResponse:
    return GmailConnectResponse(**service.connect())


@router.get("/callback")
def gmail_callback(code: str, service: ServiceDep) -> RedirectResponse:
    """Real-OAuth redirect target. Exchanges the code, then returns the user to
    the frontend settings page."""
    service.handle_callback(code)
    return RedirectResponse(url=f"{settings.FRONTEND_URL.rstrip('/')}/settings")


@router.post("/disconnect", status_code=http_status.HTTP_204_NO_CONTENT)
def gmail_disconnect(service: ServiceDep) -> None:
    service.disconnect()


@router.post("/sync", response_model=GmailSyncResponse)
def gmail_sync(service: ServiceDep) -> GmailSyncResponse:
    return GmailSyncResponse(**service.sync())


@router.get("/emails", response_model=EmailListResponse)
def list_emails(
    service: ServiceDep,
    application_id: Annotated[UUID | None, Query()] = None,
    company_id: Annotated[UUID | None, Query()] = None,
    recruiter_id: Annotated[UUID | None, Query()] = None,
    interview_id: Annotated[UUID | None, Query()] = None,
    query: Annotated[
        str | None, Query(description="Search subject, sender, or preview")
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> EmailListResponse:
    items, total = service.list_emails(
        application_id=application_id,
        company_id=company_id,
        recruiter_id=recruiter_id,
        interview_id=interview_id,
        query=query,
        skip=skip,
        limit=limit,
    )
    return EmailListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/timeline", response_model=TimelineResponse)
def application_timeline(
    service: ServiceDep,
    application_id: Annotated[UUID, Query()],
) -> TimelineResponse:
    events = service.get_timeline(application_id)
    return TimelineResponse(items=[TimelineEvent(**e) for e in events])
