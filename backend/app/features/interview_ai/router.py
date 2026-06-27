from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.interview_ai.schemas import (
    InterviewPrepListItem,
    InterviewPrepListResponse,
    InterviewPrepRequest,
    InterviewPrepResponse,
    InterviewPrepResult,
    UsageSummary,
)
from app.features.interview_ai.service import InterviewPrepService

router = APIRouter(prefix="/interview-prep", tags=["interview_ai"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> InterviewPrepService:
    return InterviewPrepService(db)


ServiceDep = Annotated[InterviewPrepService, Depends(_get_service)]


def _to_response(pkg: InterviewPrepPackage) -> InterviewPrepResponse:
    return InterviewPrepResponse(
        id=pkg.id,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
        application_id=pkg.application_id,
        resume_id=pkg.resume_id,
        company_name=pkg.company_name,
        job_title=pkg.job_title,
        interview_type=pkg.interview_type,
        interview_round=pkg.interview_round,
        job_description=pkg.job_description,
        result=InterviewPrepResult.model_validate(pkg.result),
        usage=UsageSummary(
            provider=pkg.provider,
            model=pkg.model,
            prompt_tokens=pkg.prompt_tokens,
            completion_tokens=pkg.completion_tokens,
            total_tokens=pkg.total_tokens,
            estimated_cost_usd=(
                float(pkg.estimated_cost_usd)
                if pkg.estimated_cost_usd is not None
                else None
            ),
            latency_ms=pkg.latency_ms,
        ),
    )


def _to_list_item(pkg: InterviewPrepPackage) -> InterviewPrepListItem:
    return InterviewPrepListItem(
        id=pkg.id,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
        application_id=pkg.application_id,
        company_name=pkg.company_name,
        job_title=pkg.job_title,
        interview_type=pkg.interview_type,
        interview_round=pkg.interview_round,
        provider=pkg.provider,
        model=pkg.model,
    )


@router.post(
    "/",
    response_model=InterviewPrepResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Generate and save an interview-preparation package",
)
def generate_prep(
    data: InterviewPrepRequest, service: ServiceDep
) -> InterviewPrepResponse:
    return _to_response(service.create(data))


@router.get("/", response_model=InterviewPrepListResponse)
def list_prep(
    service: ServiceDep,
    application_id: Annotated[
        UUID | None, Query(description="Filter history to a single application")
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> InterviewPrepListResponse:
    items, total = service.list(
        application_id=application_id, skip=skip, limit=limit
    )
    return InterviewPrepListResponse(
        items=[_to_list_item(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{package_id}", response_model=InterviewPrepResponse)
def get_prep(package_id: UUID, service: ServiceDep) -> InterviewPrepResponse:
    return _to_response(service.get(package_id))


@router.delete("/{package_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_prep(package_id: UUID, service: ServiceDep) -> None:
    service.delete(package_id)
