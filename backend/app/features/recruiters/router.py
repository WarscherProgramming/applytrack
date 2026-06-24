from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.recruiters.model import Recruiter
from app.features.recruiters.schema import (
    RecruiterCreate,
    RecruiterListResponse,
    RecruiterResponse,
    RecruiterUpdate,
)
from app.features.recruiters.service import RecruiterService

router = APIRouter(prefix="/recruiters", tags=["recruiters"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> RecruiterService:
    return RecruiterService(db)


ServiceDep = Annotated[RecruiterService, Depends(_get_service)]


@router.post(
    "/",
    response_model=RecruiterResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_recruiter(data: RecruiterCreate, service: ServiceDep) -> Recruiter:
    return service.create(data)


@router.get("/", response_model=RecruiterListResponse)
def list_recruiters(
    service: ServiceDep,
    query: Annotated[
        str | None,
        Query(
            description=(
                "Case-insensitive substring search across first name, "
                "last name, email, and title"
            )
        ),
    ] = None,
    company_id: Annotated[
        UUID | None,
        Query(description="Filter to recruiters associated with a specific company"),
    ] = None,
    skip: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum records to return")
    ] = 20,
) -> RecruiterListResponse:
    items, total = service.list(
        query=query,
        company_id=company_id,
        skip=skip,
        limit=limit,
    )
    return RecruiterListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{recruiter_id}", response_model=RecruiterResponse)
def get_recruiter(recruiter_id: UUID, service: ServiceDep) -> Recruiter:
    return service.get(recruiter_id)


@router.patch("/{recruiter_id}", response_model=RecruiterResponse)
def update_recruiter(
    recruiter_id: UUID,
    data: RecruiterUpdate,
    service: ServiceDep,
) -> Recruiter:
    return service.update(recruiter_id, data)


@router.delete("/{recruiter_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_recruiter(recruiter_id: UUID, service: ServiceDep) -> None:
    service.delete(recruiter_id)
