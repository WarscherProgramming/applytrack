from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.job_intelligence.schemas import JobIntelligenceResponse
from app.features.job_intelligence.service import JobIntelligenceService

router = APIRouter(prefix="/job-intelligence", tags=["job_intelligence"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> JobIntelligenceService:
    return JobIntelligenceService(db)


ServiceDep = Annotated[JobIntelligenceService, Depends(_get_service)]


@router.get("/", response_model=JobIntelligenceResponse)
def get_job_intelligence(
    service: ServiceDep,
    date_from: Annotated[str | None, Query(description="Start date, YYYY-MM-DD")] = None,
    date_to: Annotated[str | None, Query(description="End date, YYYY-MM-DD")] = None,
    industry: str | None = None,
    company: str | None = None,
    role: str | None = None,
) -> JobIntelligenceResponse:
    return service.build_report(
        date_from=date_from,
        date_to=date_to,
        industry=industry,
        company=company,
        role=role,
    )

