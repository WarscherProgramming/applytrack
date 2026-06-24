from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """
    Root Pydantic model for the entire application.

    All request bodies, response schemas, and internal DTOs inherit from this.
    Setting config here means it never has to be repeated per-schema.
    """

    model_config = ConfigDict(
        from_attributes=True,       # read data from SQLAlchemy ORM objects
        populate_by_name=True,      # accept both field name and alias in input
        str_strip_whitespace=True,  # trim accidental whitespace from all strings
    )


class TimestampSchema(AppBaseModel):
    created_at: datetime
    updated_at: datetime


class EntitySchema(TimestampSchema):
    """Base for any response schema that represents a persisted entity."""

    id: UUID
