from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.cover_letter_ai.schemas import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    CoverLetterSaveRequest,
    CoverLetterVersionsResponse,
)
from app.features.cover_letter_ai.service import CoverLetterAIService
from app.features.cover_letters.model import CoverLetter
from app.features.cover_letters.schema import CoverLetterResponse

router = APIRouter(prefix="/cover-letter-ai", tags=["cover_letter_ai"])


def _get_service(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
) -> CoverLetterAIService:
    return CoverLetterAIService(db, user.id)


ServiceDep = Annotated[CoverLetterAIService, Depends(_get_service)]


@router.post(
    "/generate",
    response_model=CoverLetterGenerateResponse,
    summary="Generate a tailored cover letter (not yet saved)",
)
def generate_cover_letter(
    data: CoverLetterGenerateRequest, service: ServiceDep
) -> CoverLetterGenerateResponse:
    return service.generate(data)


@router.post(
    "/save",
    response_model=CoverLetterResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Save a generated letter as a new version in the Cover Letter Library",
)
def save_cover_letter(
    data: CoverLetterSaveRequest, service: ServiceDep
) -> CoverLetter:
    return service.save_version(data)


@router.get(
    "/versions",
    response_model=CoverLetterVersionsResponse,
    summary="Fetch all versions (with text) of a named cover letter for comparison",
)
def list_versions(
    service: ServiceDep,
    name: Annotated[str, Query(min_length=1, description="Cover letter name")],
) -> CoverLetterVersionsResponse:
    return CoverLetterVersionsResponse(items=service.list_versions(name))
