from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.features.opportunity_discovery.schemas import JobProviderName, NormalizedJobPosting


@dataclass(frozen=True)
class ProviderFetchRequest:
    source: str
    query: str | None = None
    limit: int = 25


class JobProvider(ABC):
    """Provider seam for public job-board APIs.

    Providers fetch and normalize only. They never score, persist, or call AI.
    """

    name: JobProviderName

    @abstractmethod
    def fetch(self, request: ProviderFetchRequest) -> list[NormalizedJobPosting]:
        """Return normalized postings from one provider source."""
