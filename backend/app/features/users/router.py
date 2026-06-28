from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.features.auth.dependencies import CurrentUser
from app.features.users.model import User
from app.features.users.schemas import UserResponse, UserUpdate
from app.features.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def _get_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)


ServiceDep = Annotated[UserService, Depends(_get_service)]


@router.patch("/me", response_model=UserResponse)
def update_me(data: UserUpdate, user: CurrentUser, service: ServiceDep) -> User:
    return service.update_me(user, data)
