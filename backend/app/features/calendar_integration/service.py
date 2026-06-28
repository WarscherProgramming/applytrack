from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions.http import NotFoundError, ValidationError
from app.features.applications.model import JobApplication
from app.features.calendar_integration.model import (
    CalendarConnection,
    CalendarConnectionStatus,
    CalendarItemType,
    CalendarProvider,
    CalendarSyncEvent,
    CalendarSyncStatus,
)
from app.features.calendar_integration.providers import (
    GoogleCalendarProvider,
    OutlookCalendarProvider,
    export_ics,
)
from app.features.calendar_integration.providers.base import CalendarProviderAdapter
from app.features.calendar_integration.repository import CalendarIntegrationRepository
from app.features.calendar_integration.schemas import (
    CalendarCallbackResponse,
    CalendarConnectResponse,
    CalendarConnectionResponse,
    CalendarDisconnectResponse,
    CalendarEventPayload,
    CalendarStatusResponse,
    CalendarSyncSummary,
    ManualSyncRequest,
    SyncItemRequest,
)
from app.features.followups.model import FollowUp
from app.features.interviews.model import Interview

INACTIVE_INTERVIEW_STATUSES = {"cancelled", "no_show"}
INACTIVE_FOLLOWUP_STATUSES = {"completed", "skipped"}


class CalendarIntegrationService:
    """Coordinates deterministic ApplyTrack item sync through provider adapters."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CalendarIntegrationRepository(db)
        self.providers: dict[CalendarProvider, CalendarProviderAdapter] = {
            CalendarProvider.GOOGLE: GoogleCalendarProvider(),
            CalendarProvider.OUTLOOK: OutlookCalendarProvider(),
        }

    def status(self) -> CalendarStatusResponse:
        by_provider = {
            CalendarProvider(connection.provider): connection
            for connection in self.repo.list_connections()
        }
        connections = [
            self._connection_response(
                by_provider.get(provider)
                or CalendarConnection(
                    provider=provider.value,
                    status=CalendarConnectionStatus.DISCONNECTED.value,
                )
            )
            for provider in (CalendarProvider.GOOGLE, CalendarProvider.OUTLOOK)
        ]
        sync_events = [
            item
            for item in self.repo.list_sync_events()
            if item.status == CalendarSyncStatus.SYNCED.value
        ]
        latest = max(
            (connection for connection in by_provider.values() if connection.last_sync_at),
            key=lambda connection: connection.last_sync_at,
            default=None,
        )
        return CalendarStatusResponse(
            connections=connections,
            synced_event_count=len(sync_events),
            last_sync_at=latest.last_sync_at if latest else None,
            last_sync_status=latest.last_sync_status if latest else None,
            last_error=latest.last_error if latest else None,
        )

    def connect(self, provider: CalendarProvider) -> CalendarConnectResponse:
        adapter = self._provider(provider)
        auth_url = adapter.authorization_url(state=f"calendar:{provider.value}")
        if auth_url:
            return CalendarConnectResponse(
                provider=provider,
                authorization_url=auth_url,
                connected=False,
                message="Open the authorization URL to connect your calendar.",
            )
        self.repo.upsert_connection(
            provider,
            {
                "status": CalendarConnectionStatus.CONNECTED.value,
                "account_email": f"simulated-{provider.value}-calendar@applytrack.local",
                "calendar_id": "primary",
                "last_sync_status": "connected_simulation",
                "last_error": None,
            },
        )
        return CalendarConnectResponse(
            provider=provider,
            authorization_url=None,
            connected=True,
            message="Connected in simulation mode; no external calendar credentials required.",
        )

    def complete_oauth(
        self, provider: CalendarProvider, *, code: str | None, state: str | None
    ) -> CalendarCallbackResponse:
        self._provider(provider)
        self.repo.upsert_connection(
            provider,
            {
                "status": CalendarConnectionStatus.CONNECTED.value,
                "account_email": f"oauth-{provider.value}-calendar@applytrack.local",
                "calendar_id": "primary",
                "last_sync_status": "oauth_foundation_connected",
                "last_error": None,
            },
        )
        return CalendarCallbackResponse(
            provider=provider,
            connected=True,
            message=(
                "Calendar OAuth foundation connected. Token exchange is not "
                "enabled yet; sync runs through the provider simulation adapter."
            ),
        )

    def disconnect(self, provider: CalendarProvider) -> CalendarDisconnectResponse:
        self._provider(provider)
        self.repo.upsert_connection(
            provider,
            {
                "status": CalendarConnectionStatus.DISCONNECTED.value,
                "last_sync_status": "disconnected",
                "last_error": None,
            },
        )
        return CalendarDisconnectResponse(provider=provider, disconnected=True)

    def sync(self, request: ManualSyncRequest) -> CalendarSyncSummary:
        provider = self._provider(request.provider)
        self._require_connected(request.provider)
        return self._sync_items(
            provider=provider,
            include_interviews=request.include_interviews,
            include_followups=request.include_followups,
        )

    def sync_interview(
        self, interview_id: UUID, request: SyncItemRequest
    ) -> CalendarSyncSummary:
        provider = self._provider(request.provider)
        self._require_connected(request.provider)
        interview = self.repo.get_interview(interview_id)
        if interview is None:
            raise NotFoundError("Interview", interview_id)
        return self._sync_items(
            provider=provider,
            include_interviews=True,
            include_followups=False,
            target_item_type=CalendarItemType.INTERVIEW,
            target_item_id=str(interview_id),
        )

    def sync_followup(
        self, followup_id: UUID, request: SyncItemRequest
    ) -> CalendarSyncSummary:
        provider = self._provider(request.provider)
        self._require_connected(request.provider)
        followup = self.repo.get_followup(followup_id)
        if followup is None:
            raise NotFoundError("Follow-up", followup_id)
        return self._sync_items(
            provider=provider,
            include_interviews=False,
            include_followups=True,
            target_item_type=CalendarItemType.FOLLOW_UP,
            target_item_id=str(followup_id),
        )

    def ics_export(self) -> str:
        return export_ics(self._active_events(include_interviews=True, include_followups=True))

    def _sync_items(
        self,
        *,
        provider: CalendarProviderAdapter,
        include_interviews: bool,
        include_followups: bool,
        target_item_type: CalendarItemType | None = None,
        target_item_id: str | None = None,
    ) -> CalendarSyncSummary:
        now = datetime.now(UTC)
        events = self._active_events(
            include_interviews=include_interviews,
            include_followups=include_followups,
            target_item_type=target_item_type,
            target_item_id=target_item_id,
        )
        active_keys = {(event.item_type.value, event.item_id) for event in events}
        summary = CalendarSyncSummary(provider=provider.provider, last_sync_at=now)

        for event in events:
            existing = self.repo.get_sync_event(
                provider.provider, event.item_type.value, event.item_id
            )
            event_hash = _event_hash(event)
            if (
                existing
                and existing.status == CalendarSyncStatus.SYNCED.value
                and existing.event_hash == event_hash
            ):
                summary.skipped += 1
                continue
            try:
                result = provider.upsert_event(
                    event,
                    external_event_id=existing.external_event_id if existing else None,
                )
                self.repo.upsert_sync_event(
                    provider.provider,
                    {
                        "item_type": event.item_type.value,
                        "item_id": event.item_id,
                        "external_event_id": result.external_event_id,
                        "event_hash": event_hash,
                        "status": CalendarSyncStatus.SYNCED.value,
                        "last_synced_at": now,
                        "last_error": None,
                    },
                )
                if result.action == "updated" or existing:
                    summary.updated += 1
                else:
                    summary.created += 1
            except Exception as exc:  # pragma: no cover - provider boundary
                summary.errors.append(str(exc))
                if existing:
                    self.repo.mark_sync_error(existing, str(exc), now)

        scoped_events = self._scoped_sync_events(
            provider.provider,
            include_interviews=include_interviews,
            include_followups=include_followups,
            target_item_type=target_item_type,
            target_item_id=target_item_id,
        )
        for existing in scoped_events:
            key = (existing.item_type, existing.item_id)
            if key in active_keys or existing.status == CalendarSyncStatus.DELETED.value:
                continue
            try:
                provider.delete_event(existing.external_event_id)
                self.repo.upsert_sync_event(
                    provider.provider,
                    {
                        "item_type": existing.item_type,
                        "item_id": existing.item_id,
                        "external_event_id": existing.external_event_id,
                        "event_hash": existing.event_hash,
                        "status": CalendarSyncStatus.DELETED.value,
                        "last_synced_at": now,
                        "last_error": None,
                    },
                )
                summary.deleted += 1
            except Exception as exc:  # pragma: no cover - provider boundary
                summary.errors.append(str(exc))
                self.repo.mark_sync_error(existing, str(exc), now)

        self.repo.upsert_connection(
            provider.provider,
            {
                "status": CalendarConnectionStatus.CONNECTED.value,
                "last_sync_at": now,
                "last_sync_status": "error" if summary.errors else "ok",
                "last_error": "; ".join(summary.errors) if summary.errors else None,
            },
        )
        summary.synced_event_count = len(
            [
                item
                for item in self.repo.list_sync_events(provider.provider)
                if item.status == CalendarSyncStatus.SYNCED.value
            ]
        )
        return summary

    def _active_events(
        self,
        *,
        include_interviews: bool,
        include_followups: bool,
        target_item_type: CalendarItemType | None = None,
        target_item_id: str | None = None,
    ) -> list[CalendarEventPayload]:
        applications = {item.id: item for item in self.repo.list_applications()}
        events: list[CalendarEventPayload] = []
        if include_interviews and target_item_type in (None, CalendarItemType.INTERVIEW):
            events.extend(
                self._interview_event(interview, applications)
                for interview in self.repo.list_interviews()
                if self._is_target(interview.id, target_item_id)
                and interview.status not in INACTIVE_INTERVIEW_STATUSES
            )
        if include_followups and target_item_type in (None, CalendarItemType.FOLLOW_UP):
            events.extend(
                self._followup_event(followup, applications)
                for followup in self.repo.list_followups()
                if self._is_target(followup.id, target_item_id)
                and followup.status not in INACTIVE_FOLLOWUP_STATUSES
            )
        return events

    def _scoped_sync_events(
        self,
        provider: CalendarProvider,
        *,
        include_interviews: bool,
        include_followups: bool,
        target_item_type: CalendarItemType | None = None,
        target_item_id: str | None = None,
    ) -> list[CalendarSyncEvent]:
        events = self.repo.list_sync_events(provider)
        scoped: list[CalendarSyncEvent] = []
        for event in events:
            if target_item_type and event.item_type != target_item_type.value:
                continue
            if target_item_id and event.item_id != target_item_id:
                continue
            if event.item_type == CalendarItemType.INTERVIEW.value and not include_interviews:
                continue
            if event.item_type == CalendarItemType.FOLLOW_UP.value and not include_followups:
                continue
            scoped.append(event)
        return scoped

    def _interview_event(
        self, interview: Interview, applications: dict[UUID, JobApplication]
    ) -> CalendarEventPayload:
        application = applications.get(interview.application_id)
        title = f"Interview: {application.job_title if application else 'Application'}"
        location = interview.meeting_link or interview.location
        details = [f"Interview type: {interview.interview_type or 'interview'}"]
        if application:
            details.append(f"Application: {application.job_title}")
        if interview.notes:
            details.append(f"Notes: {interview.notes}")
        return CalendarEventPayload(
            item_type=CalendarItemType.INTERVIEW,
            item_id=str(interview.id),
            title=title,
            description="\n".join(details),
            location=location,
            start_at=interview.scheduled_at,
            end_at=interview.scheduled_at
            + timedelta(minutes=interview.duration_minutes),
            status=interview.status,
            source_updated_at=interview.updated_at or interview.scheduled_at,
        )

    def _followup_event(
        self, followup: FollowUp, applications: dict[UUID, JobApplication]
    ) -> CalendarEventPayload:
        application = applications.get(followup.application_id)
        start_at = datetime.combine(followup.due_date, time(hour=9), tzinfo=UTC)
        details = [followup.description or f"Follow-up type: {followup.followup_type}"]
        if application:
            details.append(f"Application: {application.job_title}")
        return CalendarEventPayload(
            item_type=CalendarItemType.FOLLOW_UP,
            item_id=str(followup.id),
            title=f"Follow-up: {followup.title}",
            description="\n".join(details),
            location=None,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=30),
            status=followup.status,
            source_updated_at=followup.updated_at or start_at,
        )

    def _provider(self, provider: CalendarProvider) -> CalendarProviderAdapter:
        if provider == CalendarProvider.ICS:
            raise ValidationError("ICS is export-only and does not support OAuth sync.")
        adapter = self.providers.get(provider)
        if adapter is None:
            raise ValidationError(f"Unsupported calendar provider: {provider.value}")
        return adapter

    def _require_connected(self, provider: CalendarProvider) -> None:
        connection = self.repo.get_connection(provider)
        if connection is None or connection.status != CalendarConnectionStatus.CONNECTED.value:
            raise ValidationError(f"Connect {provider.value} calendar before syncing.")

    @staticmethod
    def _connection_response(
        connection: CalendarConnection,
    ) -> CalendarConnectionResponse:
        return CalendarConnectionResponse.model_validate(connection)

    @staticmethod
    def _is_target(item_id: UUID, target_item_id: str | None) -> bool:
        return target_item_id is None or str(item_id) == target_item_id


def _event_hash(event: CalendarEventPayload) -> str:
    payload = json.dumps(event.model_dump(mode="json"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
