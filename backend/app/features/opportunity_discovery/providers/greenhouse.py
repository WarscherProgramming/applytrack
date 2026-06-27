from typing import Any

from app.features.opportunity_discovery.providers.base import JobProvider, ProviderFetchRequest
from app.features.opportunity_discovery.providers.common import (
    build_posting,
    get_json,
    parse_datetime,
)
from app.features.opportunity_discovery.schemas import JobProviderName, NormalizedJobPosting


class GreenhouseProvider(JobProvider):
    name = JobProviderName.GREENHOUSE

    def fetch(self, request: ProviderFetchRequest) -> list[NormalizedJobPosting]:
        board = request.source.strip().strip("/")
        if not board:
            return []
        data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
        company = str(data.get("name") or board)
        rows: list[NormalizedJobPosting] = []
        for raw in data.get("jobs", [])[: request.limit]:
            title = str(raw.get("title") or "")
            content = str(raw.get("content") or "")
            if not _matches(request.query, title, content):
                continue
            rows.append(
                build_posting(
                    provider=self.name,
                    source=board,
                    provider_job_id=raw.get("id"),
                    company=company,
                    title=title,
                    location=_greenhouse_location(raw),
                    salary=None,
                    employment_type=None,
                    job_url=str(raw.get("absolute_url") or ""),
                    posted_at=parse_datetime(raw.get("updated_at")),
                    description=content,
                )
            )
        return rows


def _greenhouse_location(raw: dict[str, Any]) -> str | None:
    location = raw.get("location")
    if isinstance(location, dict):
        name = location.get("name")
        return str(name) if name else None
    return str(location) if location else None


def _matches(query: str | None, title: str, description: str) -> bool:
    if not query:
        return True
    needle = query.lower()
    return needle in title.lower() or needle in description.lower()
