from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.tasks.model import Task, TaskPriority, TaskSource, TaskStatus
from app.features.tasks.schemas import (
    TaskCreate,
    TaskGenerationResponse,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.features.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> TaskService:
    return TaskService(db)


ServiceDep = Annotated[TaskService, Depends(_get_service)]
SkipParam = Annotated[int, Query(ge=0, description="Records to skip")]
LimitParam = Annotated[int, Query(ge=1, le=100, description="Maximum records to return")]


@router.post("/", response_model=TaskResponse, status_code=http_status.HTTP_201_CREATED)
def create_task(data: TaskCreate, service: ServiceDep) -> Task:
    return service.create(data)


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    service: ServiceDep,
    status: Annotated[TaskStatus | None, Query(description="Filter by status")] = None,
    priority: Annotated[TaskPriority | None, Query(description="Filter by priority")] = None,
    source: Annotated[TaskSource | None, Query(description="Filter by source")] = None,
    application_id: Annotated[UUID | None, Query()] = None,
    company_id: Annotated[UUID | None, Query()] = None,
    recruiter_id: Annotated[UUID | None, Query()] = None,
    interview_id: Annotated[UUID | None, Query()] = None,
    followup_id: Annotated[UUID | None, Query()] = None,
    skip: SkipParam = 0,
    limit: LimitParam = 50,
) -> TaskListResponse:
    items, total = service.list(
        status=status,
        priority=priority,
        source=source,
        application_id=application_id,
        company_id=company_id,
        recruiter_id=recruiter_id,
        interview_id=interview_id,
        followup_id=followup_id,
        skip=skip,
        limit=limit,
    )
    return TaskListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/generate/daily-briefing", response_model=TaskGenerationResponse)
def generate_daily_briefing_tasks(service: ServiceDep) -> TaskGenerationResponse:
    return service.generate_from_daily_briefing()


@router.post("/generate/overdue-followups", response_model=TaskGenerationResponse)
def generate_overdue_followup_tasks(service: ServiceDep) -> TaskGenerationResponse:
    return service.generate_from_overdue_followups()


@router.post("/generate/upcoming-interviews", response_model=TaskGenerationResponse)
def generate_upcoming_interview_tasks(service: ServiceDep) -> TaskGenerationResponse:
    return service.generate_from_upcoming_interviews()


@router.post("/generate/recruiter-emails", response_model=TaskGenerationResponse)
def generate_recruiter_email_tasks(service: ServiceDep) -> TaskGenerationResponse:
    return service.generate_from_recruiter_emails()


@router.post("/generate/all", response_model=TaskGenerationResponse)
def generate_all_tasks(service: ServiceDep) -> TaskGenerationResponse:
    return service.generate_all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, service: ServiceDep) -> Task:
    return service.get(task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, data: TaskUpdate, service: ServiceDep) -> Task:
    return service.update(task_id, data)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: UUID, service: ServiceDep) -> Task:
    return service.complete(task_id)


@router.post("/{task_id}/dismiss", response_model=TaskResponse)
def dismiss_task(task_id: UUID, service: ServiceDep) -> Task:
    return service.dismiss(task_id)


@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, service: ServiceDep) -> None:
    service.delete(task_id)
