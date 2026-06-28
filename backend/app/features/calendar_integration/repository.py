from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.applications.model import JobApplication
from app.features.calendar_integration.model import (
    CalendarConnection,
    CalendarProvider,
    CalendarSyncEvent,
)
from app.features.followups.model import FollowUp
from app.features.interviews.model import Interview


class CalendarIntegrationRepository:
    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def get_connection(self, provider: CalendarProvider) -> CalendarConnection | None:
        return self.db.scalars(
            select(CalendarConnection).where(
                CalendarConnection.provider == provider.value,
                CalendarConnection.user_id == self.user_id,
            )
        ).first()

    def upsert_connection(self, provider: CalendarProvider, data: dict) -> CalendarConnection:
        connection = self.get_connection(provider)
        if connection is None:
            connection = CalendarConnection(
                provider=provider.value,
                user_id=self.user_id,
                **data,
            )
            self.db.add(connection)
        else:
            for key, value in data.items():
                setattr(connection, key, value)
        self.db.flush()
        return connection

    def list_connections(self) -> list[CalendarConnection]:
        return list(
            self.db.scalars(
                select(CalendarConnection)
                .where(CalendarConnection.user_id == self.user_id)
                .order_by(CalendarConnection.provider)
            ).all()
        )

    def list_interviews(self) -> list[Interview]:
        return list(
            self.db.scalars(
                select(Interview)
                .where(Interview.user_id == self.user_id)
                .order_by(Interview.scheduled_at)
            ).all()
        )

    def list_followups(self) -> list[FollowUp]:
        return list(
            self.db.scalars(
                select(FollowUp)
                .where(FollowUp.user_id == self.user_id)
                .order_by(FollowUp.due_date)
            ).all()
        )

    def list_applications(self) -> list[JobApplication]:
        return list(
            self.db.scalars(
                select(JobApplication).where(JobApplication.user_id == self.user_id)
            ).all()
        )

    def get_interview(self, interview_id) -> Interview | None:
        return self.db.scalars(
            select(Interview).where(
                Interview.id == interview_id,
                Interview.user_id == self.user_id,
            )
        ).first()

    def get_followup(self, followup_id) -> FollowUp | None:
        return self.db.scalars(
            select(FollowUp).where(
                FollowUp.id == followup_id,
                FollowUp.user_id == self.user_id,
            )
        ).first()

    def get_sync_event(
        self, provider: CalendarProvider, item_type: str, item_id: str
    ) -> CalendarSyncEvent | None:
        return self.db.scalars(
            select(CalendarSyncEvent).where(
                CalendarSyncEvent.provider == provider.value,
                CalendarSyncEvent.item_type == item_type,
                CalendarSyncEvent.item_id == item_id,
                CalendarSyncEvent.user_id == self.user_id,
            )
        ).first()

    def list_sync_events(self, provider: CalendarProvider | None = None) -> list[CalendarSyncEvent]:
        stmt = select(CalendarSyncEvent).where(CalendarSyncEvent.user_id == self.user_id)
        if provider is not None:
            stmt = stmt.where(CalendarSyncEvent.provider == provider.value)
        return list(self.db.scalars(stmt.order_by(CalendarSyncEvent.created_at)).all())

    def upsert_sync_event(self, provider: CalendarProvider, data: dict) -> CalendarSyncEvent:
        existing = self.get_sync_event(provider, data["item_type"], data["item_id"])
        if existing is None:
            existing = CalendarSyncEvent(
                provider=provider.value,
                user_id=self.user_id,
                **data,
            )
            self.db.add(existing)
        else:
            for key, value in data.items():
                setattr(existing, key, value)
        self.db.flush()
        return existing

    def mark_sync_error(self, event: CalendarSyncEvent, error: str, synced_at: datetime) -> None:
        event.status = "error"
        event.last_error = error
        event.last_synced_at = synced_at
        self.db.flush()
