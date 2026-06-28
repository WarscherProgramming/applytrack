from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.features.auth.service import AuthService
from app.features.users.model import User
from app.features.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)


ServiceDep = Annotated[AuthService, Depends(_get_service)]


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def register(data: RegisterRequest, service: ServiceDep) -> TokenResponse:
    return service.register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, service: ServiceDep) -> TokenResponse:
    return service.login(data)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, service: ServiceDep) -> TokenResponse:
    return service.refresh(data)


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> User:
    return user


@router.post("/logout", response_model=LogoutResponse)
def logout(
    data: LogoutRequest,
    service: ServiceDep,
    user: CurrentUser,
) -> LogoutResponse:
    return service.logout(data, user)
