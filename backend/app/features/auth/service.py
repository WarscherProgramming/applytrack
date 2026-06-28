import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions.http import ConflictError, UnauthorizedError
from app.features.auth.repository import RefreshTokenRepository
from app.features.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.features.users.model import User
from app.features.users.repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)

    def register(self, data: RegisterRequest) -> TokenResponse:
        email = data.email.lower()
        if self.user_repo.get_by_email(email) is not None:
            raise ConflictError("User", "email", email)
        user = self.user_repo.create(
            {
                "email": email,
                "hashed_password": hash_password(data.password),
                "full_name": data.full_name,
                "is_active": True,
            }
        )
        return self._issue_tokens(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email.lower())
        if user is None or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")
        return self._issue_tokens(user)

    def refresh(self, data: RefreshRequest) -> TokenResponse:
        token = self.refresh_repo.get_valid(_token_hash(data.refresh_token))
        if token is None:
            raise UnauthorizedError("Invalid refresh token")
        user = self.user_repo.get_active(token.user_id)
        if user is None:
            raise UnauthorizedError("User account is inactive")
        self.refresh_repo.revoke(token)
        return self._issue_tokens(user)

    def logout(self, data: LogoutRequest, user: User | None = None) -> LogoutResponse:
        if data.refresh_token:
            token = self.refresh_repo.get_valid(_token_hash(data.refresh_token))
            if token is not None:
                self.refresh_repo.revoke(token)
            return LogoutResponse(logged_out=True)
        if user is not None:
            self.refresh_repo.revoke_all_for_user(user)
        return LogoutResponse(logged_out=True)

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id))
        refresh_token = secrets.token_urlsafe(48)
        self.refresh_repo.create(
            {
                "user_id": user.id,
                "token_hash": _token_hash(refresh_token),
                "expires_at": datetime.now(UTC)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            }
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user,
        )


def parse_user_id(subject: str | None) -> UUID:
    if subject is None:
        raise UnauthorizedError()
    try:
        return UUID(subject)
    except ValueError as exc:
        raise UnauthorizedError() from exc


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
