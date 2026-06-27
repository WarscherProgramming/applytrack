from pydantic import Field

from app.shared.base_schema import AppBaseModel, EntitySchema


class DocumentUpdate(AppBaseModel):
    """PATCH body for a stored document — rename and/or edit notes.

    File content is immutable: re-uploading creates a new version rather than
    mutating an existing record, so only metadata is editable here. Every field
    is optional; the service uses model_dump(exclude_unset=True).
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=5000)


class DocumentResponse(EntitySchema):
    name: str
    file_name: str
    storage_path: str
    version: int
    notes: str | None


class DocumentListResponse(AppBaseModel):
    items: list[DocumentResponse]
    total: int
    skip: int
    limit: int
