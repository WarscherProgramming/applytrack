from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.features.calendar_integration.model import CalendarProvider
from app.features.calendar_integration.schemas import CalendarEventPayload


@dataclass(frozen=True)
class ProviderEventResult:
    external_event_id: str
    action: str


class CalendarProviderAdapter(ABC):
    provider: CalendarProvider

    @abstractmethod
    def authorization_url(self, *, state: str | None = None) -> str | None:
        """Return an OAuth URL when the provider is configured."""

    @abstractmethod
    def upsert_event(
        self,
        event: CalendarEventPayload,
        *,
        external_event_id: str | None = None,
    ) -> ProviderEventResult:
        """Create or update an external calendar event."""

    @abstractmethod
    def delete_event(self, external_event_id: str) -> None:
        """Delete or mark an external calendar event cancelled."""
