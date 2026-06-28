import hashlib

from app.features.calendar_integration.model import CalendarProvider
from app.features.calendar_integration.providers.base import (
    CalendarProviderAdapter,
    ProviderEventResult,
)
from app.features.calendar_integration.schemas import CalendarEventPayload


class OutlookCalendarProvider(CalendarProviderAdapter):
    provider = CalendarProvider.OUTLOOK

    def authorization_url(self, *, state: str | None = None) -> str | None:
        # Foundation only: no Microsoft app settings exist yet, so expose a
        # simulation-mode connection instead of pretending real OAuth is ready.
        return None

    def upsert_event(
        self,
        event: CalendarEventPayload,
        *,
        external_event_id: str | None = None,
    ) -> ProviderEventResult:
        event_id = external_event_id or _simulated_id(self.provider.value, event)
        return ProviderEventResult(
            external_event_id=event_id,
            action="updated" if external_event_id else "created",
        )

    def delete_event(self, external_event_id: str) -> None:
        return None


def _simulated_id(provider: str, event: CalendarEventPayload) -> str:
    raw = f"{provider}:{event.item_type}:{event.item_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()
