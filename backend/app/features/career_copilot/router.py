from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.career_copilot.schemas import CareerCopilotResponse
from app.features.career_copilot.service import CareerCopilotService

router = APIRouter(prefix="/career-copilot", tags=["career_copilot"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> CareerCopilotService:
    return CareerCopilotService(db)


ServiceDep = Annotated[CareerCopilotService, Depends(_get_service)]


@router.get("/daily", response_model=CareerCopilotResponse)
def get_daily_briefing(service: ServiceDep) -> CareerCopilotResponse:
    return service.build_daily_briefing()

