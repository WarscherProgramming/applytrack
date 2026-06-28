from pydantic import EmailStr, Field, field_validator

from app.features.users.schemas import UserResponse
from app.shared.base_schema import AppBaseModel


class RegisterRequest(AppBaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.islower() for char in value):
            raise ValueError("Password must include a lowercase letter")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include an uppercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include a number")
        return value


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
