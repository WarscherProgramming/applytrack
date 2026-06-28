from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resume_match.schema import (
    ResumeMatchCreate,
    ResumeMatchListItem,
    ResumeMatchListResponse,
    ResumeMatchResponse,
)
from app.features.resume_match.service import ResumeMatchService

router = APIRouter(prefix="/resume-match", tags=["resume_match"])

# How much of the job description is echoed in the lightweight history list.
_PREVIEW_CHARS = 160


def _get_service(
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
) -> ResumeMatchService:
    return ResumeMatchService(db, user.id)


ServiceDep = Annotated[ResumeMatchService, Depends(_get_service)]


def _to_list_item(analysis: ResumeMatchAnalysis) -> ResumeMatchListItem:
    preview = analysis.job_description[:_PREVIEW_CHARS]
    if len(analysis.job_description) > _PREVIEW_CHARS:
        preview = preview.rstrip() + "…"
    return ResumeMatchListItem(
        id=analysis.id,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        resume_id=analysis.resume_id,
        resume_name=analysis.resume_name,
        overall_match_score=analysis.overall_match_score,
        job_description_preview=preview,
        provider=analysis.provider,
        model=analysis.model,
    )


@router.post(
    "/",
    response_model=ResumeMatchResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Run a resume-vs-job-description match analysis",
)
def run_analysis(
    data: ResumeMatchCreate, service: ServiceDep
) -> ResumeMatchAnalysis:
    return service.create(data)


@router.get("/", response_model=ResumeMatchListResponse)
def list_analyses(
    service: ServiceDep,
    resume_id: Annotated[
        UUID | None, Query(description="Filter history to a single resume")
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ResumeMatchListResponse:
    items, total = service.list(resume_id=resume_id, skip=skip, limit=limit)
    return ResumeMatchListResponse(
        items=[_to_list_item(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{analysis_id}", response_model=ResumeMatchResponse)
def get_analysis(analysis_id: UUID, service: ServiceDep) -> ResumeMatchAnalysis:
    return service.get(analysis_id)


@router.delete("/{analysis_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: UUID, service: ServiceDep) -> None:
    service.delete(analysis_id)
