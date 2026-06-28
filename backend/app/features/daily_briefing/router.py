from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.daily_briefing.model import Notification
from app.features.daily_briefing.schemas import (
    DailyBriefingResponse,
    NotificationListResponse,
    NotificationResponse,
    NotificationUpdate,
)
from app.features.daily_briefing.service import DailyBriefingService

router = APIRouter(prefix="/daily-briefing", tags=["daily_briefing"])


def _get_service(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
) -> DailyBriefingService:
    return DailyBriefingService(db, user.id)


ServiceDep = Annotated[DailyBriefingService, Depends(_get_service)]


@router.get("/", response_model=DailyBriefingResponse)
def get_daily_briefing(service: ServiceDep) -> DailyBriefingResponse:
    return service.build_briefing()


@router.post("/refresh", response_model=DailyBriefingResponse)
def refresh_daily_briefing(service: ServiceDep) -> DailyBriefingResponse:
    return service.build_briefing()


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    service: ServiceDep,
    include_dismissed: Annotated[bool, Query()] = False,
    unread_only: Annotated[bool, Query()] = False,
    pinned_only: Annotated[bool, Query()] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> NotificationListResponse:
    return service.list_notifications(
        include_dismissed=include_dismissed,
        unread_only=unread_only,
        pinned_only=pinned_only,
        skip=skip,
        limit=limit,
    )


@router.patch("/notifications/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: UUID,
    data: NotificationUpdate,
    service: ServiceDep,
) -> Notification:
    return service.update_notification(notification_id, data)
