from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.exceptions.http import UnauthorizedError
from app.features.auth.service import parse_user_id
from app.features.users.model import User
from app.features.users.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    user_id = parse_user_id(decode_access_token(credentials.credentials))
    user = UserRepository(db).get_active(user_id)
    if user is None:
        raise UnauthorizedError()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
