from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.opportunity_discovery.schemas import (
    OpportunitySearchRequest,
    OpportunitySearchResponse,
    SaveOpportunityRequest,
    SaveOpportunityResponse,
)
from app.features.opportunity_discovery.service import OpportunityDiscoveryService

router = APIRouter(prefix="/opportunity-discovery", tags=["opportunity_discovery"])


def _get_service(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
) -> OpportunityDiscoveryService:
    return OpportunityDiscoveryService(db, user.id)


ServiceDep = Annotated[OpportunityDiscoveryService, Depends(_get_service)]


@router.post("/search", response_model=OpportunitySearchResponse)
def search_opportunities(
    data: OpportunitySearchRequest,
    service: ServiceDep,
) -> OpportunitySearchResponse:
    return service.search(data)


@router.post(
    "/save",
    response_model=SaveOpportunityResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def save_opportunity(
    data: SaveOpportunityRequest,
    service: ServiceDep,
) -> SaveOpportunityResponse:
    return service.save(data)
