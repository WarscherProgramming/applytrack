from pydantic import EmailStr, Field, field_validator

from app.core.security import validate_strong_password
from app.features.users.schemas import UserResponse
from app.shared.base_schema import AppBaseModel


class RegisterRequest(AppBaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)


class LoginRequest(AppBaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class RefreshRequest(AppBaseModel):
    refresh_token: str = Field(..., min_length=20)


class LogoutRequest(AppBaseModel):
    refresh_token: str | None = Field(None, min_length=20)


class TokenResponse(AppBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(AppBaseModel):
    logged_out: bool
