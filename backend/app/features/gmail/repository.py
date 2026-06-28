import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.gmail.models import EmailMessage, GmailAccount

logger = logging.getLogger(__name__)


class GmailAccountRepository:
    """Single-account today; queries the first/only row. Never commits."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_account(self, user_id: UUID) -> GmailAccount | None:
        stmt = select(GmailAccount).where(GmailAccount.user_id == user_id).limit(1)
        return self.db.scalars(stmt).first()

    def create(self, data: dict[str, Any]) -> GmailAccount:
        account = GmailAccount(**data)
        self.db.add(account)
        self.db.flush()
        return account

    def update(self, account: GmailAccount, data: dict[str, Any]) -> GmailAccount:
        for key, value in data.items():
            setattr(account, key, value)
        self.db.flush()
        return account

    def delete(self, account: GmailAccount) -> None:
        self.db.delete(account)
        self.db.flush()


class EmailMessageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_message_id(
        self, account_id: UUID, message_id: str
    ) -> EmailMessage | None:
        stmt = select(EmailMessage).where(
            EmailMessage.account_id == account_id,
            EmailMessage.message_id == message_id,
        )
        return self.db.scalars(stmt).first()

    def create(self, data: dict[str, Any]) -> EmailMessage:
        email = EmailMessage(**data)
        self.db.add(email)
        self.db.flush()
        return email

    def update(self, email: EmailMessage, data: dict[str, Any]) -> EmailMessage:
        for key, value in data.items():
            setattr(email, key, value)
        self.db.flush()
        return email

    def list_filtered(
        self,
        *,
        application_id: UUID | None = None,
        company_id: UUID | None = None,
        recruiter_id: UUID | None = None,
        interview_id: UUID | None = None,
        query: str | None = None,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmailMessage], int]:
        base = select(EmailMessage).where(EmailMessage.user_id == user_id)

        if application_id is not None:
            base = base.where(EmailMessage.application_id == application_id)
        if company_id is not None:
            base = base.where(EmailMessage.company_id == company_id)
        if recruiter_id is not None:
            base = base.where(EmailMessage.recruiter_id == recruiter_id)
        if interview_id is not None:
            base = base.where(EmailMessage.interview_id == interview_id)
        if query:
            pattern = f"%{query}%"
            base = base.where(
                or_(
                    EmailMessage.subject.ilike(pattern),
                    EmailMessage.sender.ilike(pattern),
                    EmailMessage.body_preview.ilike(pattern),
                )
            )

        total = (
            self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        )
        items = list(
            self.db.scalars(
                base.order_by(EmailMessage.sent_at.desc())
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total

    def all_for_account(self, account_id: UUID, user_id: UUID) -> list[EmailMessage]:
        stmt = select(EmailMessage).where(
            EmailMessage.account_id == account_id,
            EmailMessage.user_id == user_id,
        )
        return list(self.db.scalars(stmt).all())
