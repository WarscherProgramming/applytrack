from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.users.model import User
from app.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalars(select(User).where(User.email == email.lower())).first()

    def get_active(self, user_id: UUID) -> User | None:
        return self.db.scalars(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        ).first()
