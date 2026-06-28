from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.features.tasks.model import TaskPriority, TaskSource, TaskStatus
from app.shared.base_schema import AppBaseModel, EntitySchema


class TaskBase(AppBaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    completed_at: datetime | None = None
    source: TaskSource = TaskSource.MANUAL
    application_id: UUID | None = None
    company_id: UUID | None = None
    recruiter_id: UUID | None = None
    interview_id: UUID | None = None
    followup_id: UUID | None = None
    opportunity_id: str | None = Field(None, max_length=255)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(AppBaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    completed_at: datetime | None = None
    source: TaskSource | None = None
    application_id: UUID | None = None
    company_id: UUID | None = None
    recruiter_id: UUID | None = None
    interview_id: UUID | None = None
    followup_id: UUID | None = None
    opportunity_id: str | None = Field(None, max_length=255)


class TaskResponse(EntitySchema):
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    completed_at: datetime | None
    source: TaskSource
    application_id: UUID | None
    company_id: UUID | None
    recruiter_id: UUID | None
    interview_id: UUID | None
    followup_id: UUID | None
    opportunity_id: str | None
    source_key: str | None


class TaskListResponse(AppBaseModel):
    items: list[TaskResponse]
    total: int
    skip: int
    limit: int


class TaskGenerationResponse(AppBaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    items: list[TaskResponse] = Field(default_factory=list)
