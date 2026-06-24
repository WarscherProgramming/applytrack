from pydantic import Field

from app.shared.base_schema import AppBaseModel, EntitySchema


class CompanyBase(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    website: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    notes: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(AppBaseModel):
    """
    All fields are optional — only provided fields are written to the database.
    The service uses model_dump(exclude_unset=True) to determine which fields
    were explicitly sent vs. which were left at their default of None.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    website: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    notes: str | None = None


class CompanyResponse(EntitySchema):
    name: str
    website: str | None
    industry: str | None
    location: str | None
    notes: str | None


class CompanyListResponse(AppBaseModel):
    items: list[CompanyResponse]
    total: int
    skip: int
    limit: int
