from datetime import date
from uuid import UUID

from pydantic import Field

from app.features.applications.model import ApplicationStatus
from app.shared.base_schema import AppBaseModel, EntitySchema


class ApplicationBase(AppBaseModel):
    company_id: UUID
    job_title: str = Field(..., min_length=1, max_length=255)
    job_link: str | None = Field(None, max_length=2000)
    location: str | None = Field(None, max_length=255)
    salary_range: str | None = Field(None, max_length=255)
    status: ApplicationStatus = ApplicationStatus.DRAFT
    date_applied: date | None = None
    source: str | None = Field(None, max_length=255)
    notes: str | None = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(AppBaseModel):
    """All fields optional — only provided fields are written to the database.

    The service uses model_dump(exclude_unset=True) so omitted fields are
    never touched, and sending null explicitly clears a nullable field.
    """

    company_id: UUID | None = None
    job_title: str | None = Field(None, min_length=1, max_length=255)
    job_link: str | None = Field(None, max_length=2000)
    location: str | None = Field(None, max_length=255)
    salary_range: str | None = Field(None, max_length=255)
    status: ApplicationStatus | None = None
    date_applied: date | None = None
    source: str | None = Field(None, max_length=255)
    notes: str | None = None


class ApplicationResponse(EntitySchema):
    company_id: UUID
    job_title: str
    job_link: str | None
    location: str | None
    salary_range: str | None
    status: ApplicationStatus
    date_applied: date | None
    source: str | None
    notes: str | None


class ApplicationListResponse(AppBaseModel):
    items: list[ApplicationResponse]
    total: int
    skip: int
    limit: int
