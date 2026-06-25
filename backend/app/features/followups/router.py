from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.followups.model import (
    FollowUp,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)
from app.features.followups.schema import (
    FollowUpCreate,
    FollowUpListResponse,
    FollowUpResponse,
    FollowUpUpdate,
)
from app.features.followups.service import FollowUpService

router = APIRouter(prefix="/followups", tags=["followups"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> FollowUpService:
    return FollowUpService(db)


ServiceDep = Annotated[FollowUpService, Depends(_get_service)]

# Reusable pagination params for the reminder endpoints below.
SkipParam = Annotated[int, Query(ge=0, description="Records to skip")]
LimitParam = Annotated[int, Query(ge=1, le=100, description="Maximum records to return")]


@router.post(
    "/",
    response_model=FollowUpResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_followup(data: FollowUpCreate, service: ServiceDep) -> FollowUp:
    return service.create(data)


@router.get("/", response_model=FollowUpListResponse)
def list_followups(
    service: ServiceDep,
    application_id: Annotated[
        UUID | None, Query(description="Filter to a specific application")
    ] = None,
    recruiter_id: Annotated[
        UUID | None, Query(description="Filter to a specific recruiter")
    ] = None,
    interview_id: Annotated[
        UUID | None, Query(description="Filter to a specific interview")
    ] = None,
    # `status` matches the query-param name; the http_status alias above
    # prevents shadowing the fastapi.status module.
    status: Annotated[
        FollowUpStatus | None, Query(description="Filter by status")
    ] = None,
    priority: Annotated[
        FollowUpPriority | None, Query(description="Filter by priority")
    ] = None,
    followup_type: Annotated[
        FollowUpType | None, Query(description="Filter by follow-up type")
    ] = None,
    skip: SkipParam = 0,
    limit: LimitParam = 20,
) -> FollowUpListResponse:
    items, total = service.list(
        application_id=application_id,
        recruiter_id=recruiter_id,
        interview_id=interview_id,
        status=status,
        priority=priority,
        followup_type=followup_type,
        skip=skip,
        limit=limit,
    )
    return FollowUpListResponse(items=items, total=total, skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# Reminder endpoints — MUST be declared before "/{followup_id}" so that the
# static paths are matched first. If declared after, FastAPI would try to parse
# "overdue"/"today"/"upcoming" as a UUID path param and return 422.
# ---------------------------------------------------------------------------


@router.get("/overdue", response_model=FollowUpListResponse)
def list_overdue_followups(
    service: ServiceDep,
    skip: SkipParam = 0,
    limit: LimitParam = 20,
) -> FollowUpListResponse:
    """Pending follow-ups whose due_date is before today (UTC)."""
    items, total = service.list(overdue=True, skip=skip, limit=limit)
    return FollowUpListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/today", response_model=FollowUpListResponse)
def list_today_followups(
    service: ServiceDep,
    skip: SkipParam = 0,
    limit: LimitParam = 20,
) -> FollowUpListResponse:
    """Pending follow-ups due today (UTC)."""
    items, total = service.list(due_today=True, skip=skip, limit=limit)
    return FollowUpListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/upcoming", response_model=FollowUpListResponse)
def list_upcoming_followups(
    service: ServiceDep,
    skip: SkipParam = 0,
    limit: LimitParam = 20,
) -> FollowUpListResponse:
    """Pending follow-ups due within the next 7 days (today through +6, UTC)."""
    items, total = service.list(due_this_week=True, skip=skip, limit=limit)
    return FollowUpListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{followup_id}", response_model=FollowUpResponse)
def get_followup(followup_id: UUID, service: ServiceDep) -> FollowUp:
    return service.get(followup_id)


@router.patch("/{followup_id}", response_model=FollowUpResponse)
def update_followup(
    followup_id: UUID,
    data: FollowUpUpdate,
    service: ServiceDep,
) -> FollowUp:
    return service.update(followup_id, data)


@router.delete("/{followup_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_followup(followup_id: UUID, service: ServiceDep) -> None:
    service.delete(followup_id)
