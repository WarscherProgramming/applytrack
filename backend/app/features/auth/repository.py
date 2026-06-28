from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.auth.model import RefreshToken
from app.features.users.model import User
from app.shared.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(RefreshToken, db)

    def get_valid(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalars(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        ).first()

    def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.revoked_at = datetime.now(UTC)
        self.db.flush()
        return refresh_token

    def revoke_all_for_user(self, user: User) -> None:
        for token in self.db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
        ):
            token.revoked_at = datetime.now(UTC)
        self.db.flush()
