from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.career_intelligence.schemas import CareerIntelligenceResponse
from app.features.career_intelligence.service import CareerIntelligenceService

router = APIRouter(prefix="/career-intelligence", tags=["career_intelligence"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> CareerIntelligenceService:
    return CareerIntelligenceService(db)


ServiceDep = Annotated[CareerIntelligenceService, Depends(_get_service)]


@router.get("/", response_model=CareerIntelligenceResponse)
def get_career_intelligence(
    service: ServiceDep,
    date_from: Annotated[
        str | None,
        Query(description="Inclusive application/activity start date, YYYY-MM-DD"),
    ] = None,
    date_to: Annotated[
        str | None,
        Query(description="Inclusive application/activity end date, YYYY-MM-DD"),
    ] = None,
    compare_date_from: Annotated[
        str | None,
        Query(description="Optional comparison period start date, YYYY-MM-DD"),
    ] = None,
    compare_date_to: Annotated[
        str | None,
        Query(description="Optional comparison period end date, YYYY-MM-DD"),
    ] = None,
) -> CareerIntelligenceResponse:
    return service.build_dashboard(
        date_from=date_from,
        date_to=date_to,
        compare_date_from=compare_date_from,
        compare_date_to=compare_date_to,
    )

