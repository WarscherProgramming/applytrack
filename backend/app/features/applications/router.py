from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.applications.schema import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationUpdate,
)
from app.features.applications.service import ApplicationService
from app.features.auth.dependencies import CurrentUser

router = APIRouter(prefix="/applications", tags=["applications"])


def _get_service(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
) -> ApplicationService:
    return ApplicationService(db, user.id)


ServiceDep = Annotated[ApplicationService, Depends(_get_service)]


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_application(data: ApplicationCreate, service: ServiceDep) -> JobApplication:
    return service.create(data)


@router.get("/", response_model=ApplicationListResponse)
def list_applications(
    service: ServiceDep,
    query: Annotated[
        str | None,
        Query(description="Filter by job title (case-insensitive substring match)"),
    ] = None,
    # Named `status` to match the query-param name; `http_status` alias above
    # prevents this from shadowing the fastapi.status module.
    status: Annotated[
        ApplicationStatus | None,
        Query(description="Filter by application status"),
    ] = None,
    company_id: Annotated[
        UUID | None,
        Query(description="Filter to applications for a specific company"),
    ] = None,
    skip: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum records to return"),
    ] = 20,
) -> ApplicationListResponse:
    items, total = service.list(
        query=query,
        status=status,
        company_id=company_id,
        skip=skip,
        limit=limit,
    )
    return ApplicationListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: UUID, service: ServiceDep) -> JobApplication:
    return service.get(application_id)


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    service: ServiceDep,
) -> JobApplication:
    return service.update(application_id, data)


@router.delete("/{application_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_application(application_id: UUID, service: ServiceDep) -> None:
    service.delete(application_id)
