from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions.http import ConflictError
from app.features.users.model import User
from app.features.users.repository import UserRepository
from app.features.users.schemas import UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def get(self, user_id: UUID) -> User:
        return self.repo.get_or_raise(user_id)

    def update_me(self, user: User, data: UserUpdate) -> User:
        updates = data.model_dump(exclude_unset=True)
        if "email" in updates and updates["email"] is not None:
            email = updates["email"].lower()
            existing = self.repo.get_by_email(email)
            if existing is not None and existing.id != user.id:
                raise ConflictError("User", "email", email)
            updates["email"] = email
        return self.repo.update(user, updates)
