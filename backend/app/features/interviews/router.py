from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.interviews.model import Interview, InterviewStatus, InterviewType
from app.features.interviews.schema import (
    InterviewCreate,
    InterviewListResponse,
    InterviewResponse,
    InterviewUpdate,
)
from app.features.interviews.service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> InterviewService:
    return InterviewService(db)


ServiceDep = Annotated[InterviewService, Depends(_get_service)]


@router.post(
    "/",
    response_model=InterviewResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_interview(data: InterviewCreate, service: ServiceDep) -> Interview:
    return service.create(data)


@router.get("/", response_model=InterviewListResponse)
def list_interviews(
    service: ServiceDep,
    application_id: Annotated[
        UUID | None,
        Query(description="Filter to interviews for a specific application"),
    ] = None,
    recruiter_id: Annotated[
        UUID | None,
        Query(description="Filter to interviews involving a specific recruiter"),
    ] = None,
    # Named `status` to match the query-param; `http_status` alias above
    # prevents shadowing the fastapi.status module.
    status: Annotated[
        InterviewStatus | None,
        Query(description="Filter by interview status"),
    ] = None,
    interview_type: Annotated[
        InterviewType | None,
        Query(description="Filter by interview type"),
    ] = None,
    skip: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum records to return")
    ] = 20,
) -> InterviewListResponse:
    items, total = service.list(
        application_id=application_id,
        recruiter_id=recruiter_id,
        status=status,
        interview_type=interview_type,
        skip=skip,
        limit=limit,
    )
    return InterviewListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(interview_id: UUID, service: ServiceDep) -> Interview:
    return service.get(interview_id)


@router.patch("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: UUID,
    data: InterviewUpdate,
    service: ServiceDep,
) -> Interview:
    return service.update(interview_id, data)


@router.delete("/{interview_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_interview(interview_id: UUID, service: ServiceDep) -> None:
    service.delete(interview_id)
