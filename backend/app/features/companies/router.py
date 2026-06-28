from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.companies.model import Company
from app.features.companies.schema import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.features.companies.service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


def _get_service(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
) -> CompanyService:
    return CompanyService(db, user.id)


# Type alias keeps route signatures terse and readable.
ServiceDep = Annotated[CompanyService, Depends(_get_service)]


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(data: CompanyCreate, service: ServiceDep) -> Company:
    return service.create(data)


@router.get("/", response_model=CompanyListResponse)
def list_companies(
    service: ServiceDep,
    query: Annotated[
        str | None,
        Query(description="Filter by company name (case-insensitive substring match)"),
    ] = None,
    skip: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum records to return")
    ] = 20,
) -> CompanyListResponse:
    items, total = service.list(query=query, skip=skip, limit=limit)
    return CompanyListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: UUID, service: ServiceDep) -> Company:
    return service.get(company_id)


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    service: ServiceDep,
) -> Company:
    return service.update(company_id, data)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: UUID, service: ServiceDep) -> None:
    service.delete(company_id)
