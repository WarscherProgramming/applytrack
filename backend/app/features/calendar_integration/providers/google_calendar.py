import hashlib
from urllib.parse import urlencode

from app.core.config import settings
from app.features.calendar_integration.model import CalendarProvider
from app.features.calendar_integration.providers.base import (
    CalendarProviderAdapter,
    ProviderEventResult,
)
from app.features.calendar_integration.schemas import CalendarEventPayload


class GoogleCalendarProvider(CalendarProviderAdapter):
    provider = CalendarProvider.GOOGLE

    def authorization_url(self, *, state: str | None = None) -> str | None:
        if not settings.GOOGLE_CLIENT_ID:
            return None
        scope = "https://www.googleapis.com/auth/calendar.events"
        params = urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
                "response_type": "code",
                "scope": scope,
                "state": state or "applytrack-calendar",
                "access_type": "offline",
                "prompt": "consent",
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

    def upsert_event(
        self,
        event: CalendarEventPayload,
        *,
        external_event_id: str | None = None,
    ) -> ProviderEventResult:
        # Simulation-mode foundation: deterministic external ids keep sync
        # idempotent until real OAuth token exchange/API calls are introduced.
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
