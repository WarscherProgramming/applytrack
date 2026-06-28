from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.ai.usage_tracker import AIUsageRecord
from app.features.applications.model import JobApplication
from app.features.auth.model import RefreshToken
from app.features.auth.repository import RefreshTokenRepository
from app.features.calendar_integration.model import CalendarConnection, CalendarSyncEvent
from app.features.companies.model import Company
from app.features.cover_letters.model import CoverLetter
from app.features.daily_briefing.model import Notification
from app.features.followups.model import FollowUp
from app.features.gmail.models import EmailMessage, GmailAccount
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.interviews.model import Interview
from app.features.recruiters.model import Recruiter
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.model import Resume
from app.features.settings.model import UserSettings
from app.features.tasks.model import Task
from app.features.users.model import User
from app.shared.base_repository import BaseRepository


class SettingsRepository(BaseRepository[UserSettings]):
    def __init__(self, db: Session) -> None:
        super().__init__(UserSettings, db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def get_for_user_id(self, user_id: UUID) -> UserSettings | None:
        return self.db.scalars(
            select(UserSettings).where(UserSettings.user_id == user_id)
        ).first()

    def get_or_create_for_user(self, user: User) -> UserSettings:
        existing = self.get_for_user_id(user.id)
        if existing is not None:
            return existing
        return self.create({"user_id": user.id, "notification_preferences": {}})

    def list_sessions(self, user: User) -> list[RefreshToken]:
        return self.refresh_tokens.list_for_user(user)

    def get_session_by_hash(self, user: User, token_hash: str) -> RefreshToken | None:
        return self.refresh_tokens.get_for_user_by_hash(user, token_hash)

    def revoke_session(self, session: RefreshToken) -> RefreshToken:
        return self.refresh_tokens.revoke(session)

    def revoke_all_sessions(self, user: User) -> int:
        sessions = [
            token
            for token in self.refresh_tokens.list_active_for_user(user)
            if token.revoked_at is None
        ]
        self.refresh_tokens.revoke_all_for_user(user)
        return len(sessions)

    def revoke_old_sessions(self, user: User, current_token_hash: str | None = None) -> int:
        active = [
            token
            for token in self.refresh_tokens.list_active_for_user(user)
            if token.revoked_at is None
        ]
        if current_token_hash:
            self.refresh_tokens.revoke_all_for_user_except_hash(user, current_token_hash)
            return sum(1 for token in active if token.token_hash != current_token_hash)
        self.refresh_tokens.revoke_all_for_user(user)
        return len(active)

    def export_data(self, user: User) -> dict[str, list[dict[str, Any]]]:
        return {
            "companies": self._export(select(Company).where(Company.user_id == user.id)),
            "applications": self._export(
                select(JobApplication).where(JobApplication.user_id == user.id)
            ),
            "recruiters": self._export(
                select(Recruiter).where(Recruiter.user_id == user.id)
            ),
            "interviews": self._export(select(Interview).where(Interview.user_id == user.id)),
            "followups": self._export(select(FollowUp).where(FollowUp.user_id == user.id)),
            "resumes": self._export(select(Resume).where(Resume.user_id == user.id)),
            "cover_letters": self._export(
                select(CoverLetter).where(CoverLetter.user_id == user.id)
            ),
            "tasks": self._export(select(Task).where(Task.user_id == user.id)),
            "notifications": self._export(
                select(Notification).where(Notification.user_id == user.id)
            ),
            "gmail_accounts": self._export(
                select(GmailAccount).where(GmailAccount.user_id == user.id),
                exclude={"access_token_encrypted", "refresh_token_encrypted"},
            ),
            "email_messages": self._export(
                select(EmailMessage).where(EmailMessage.user_id == user.id)
            ),
            "calendar_connections": self._export(
                select(CalendarConnection).where(CalendarConnection.user_id == user.id),
                exclude={"access_token_encrypted", "refresh_token_encrypted"},
            ),
            "calendar_sync_events": self._export(
                select(CalendarSyncEvent).where(CalendarSyncEvent.user_id == user.id)
            ),
            "resume_match_analyses": self._export(
                select(ResumeMatchAnalysis).where(ResumeMatchAnalysis.user_id == user.id)
            ),
            "interview_prep_packages": self._export(
                select(InterviewPrepPackage).where(InterviewPrepPackage.user_id == user.id)
            ),
            "ai_usage_records": self._export(
                select(AIUsageRecord).where(AIUsageRecord.user_id == user.id)
            ),
        }

    def _export(
        self,
        stmt: Select,
        *,
        exclude: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.db.scalars(stmt).all()
        return [_serialize_model(row, exclude=exclude or set()) for row in rows]


def _serialize_model(instance: Any, *, exclude: set[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for column in instance.__table__.columns:
        name = column.name
        if name in exclude or name == "user_id":
            continue
        value = getattr(instance, name)
        data[name] = _jsonable(value)
    return data


def _jsonable(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return value
