from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.base_schema import AppBaseModel


class UserResponse(AppBaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(AppBaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=255)
