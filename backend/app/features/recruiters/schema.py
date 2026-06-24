from uuid import UUID

from pydantic import EmailStr, Field, model_validator
from typing_extensions import Self

from app.shared.base_schema import AppBaseModel, EntitySchema


class RecruiterBase(AppBaseModel):
    """Shared field definitions used by both create and update schemas.

    All fields are optional at the base level because RecruiterUpdate
    inherits them without adding requirements. RecruiterCreate layers a
    model_validator on top to enforce the "at least one identifier" rule.
    """

    company_id: UUID | None = None
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    # EmailStr validates format using email-validator (pydantic[email] dep).
    # Normalises the address (lowercases domain) before storing.
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    title: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=2000)
    notes: str | None = None


class RecruiterCreate(RecruiterBase):
    @model_validator(mode="after")
    def require_at_least_one_identifier(self) -> Self:
        """Reject requests that provide no way to identify the recruiter.

        A recruiter with no name and no email cannot be meaningfully
        distinguished from another recruiter, and would be unsearchable.
        The rule lives here (not in RecruiterBase) so that RecruiterUpdate
        can skip it — the service validates the merged state on updates.
        """
        if not self.first_name and not self.last_name and not self.email:
            raise ValueError(
                "at least one of first_name, last_name, or email must be provided"
            )
        return self


class RecruiterUpdate(RecruiterBase):
    """PATCH schema — every field is optional and unset fields are ignored.

    The service uses model_dump(exclude_unset=True) to build the update dict,
    then merges it with the current record before re-checking the
    'at least one identifier' invariant.
    """
    pass


class RecruiterResponse(EntitySchema):
    company_id: UUID | None
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    title: str | None
    linkedin_url: str | None
    notes: str | None


class RecruiterListResponse(AppBaseModel):
    items: list[RecruiterResponse]
    total: int
    skip: int
    limit: int
