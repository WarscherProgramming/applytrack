from typing import Any

from app.features.opportunity_discovery.providers.base import JobProvider, ProviderFetchRequest
from app.features.opportunity_discovery.providers.common import (
    build_posting,
    get_json,
    parse_datetime,
)
from app.features.opportunity_discovery.schemas import JobProviderName, NormalizedJobPosting


class AshbyProvider(JobProvider):
    name = JobProviderName.ASHBY

    def fetch(self, request: ProviderFetchRequest) -> list[NormalizedJobPosting]:
        board = request.source.strip().strip("/")
        if not board:
            return []
        data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        rows: list[NormalizedJobPosting] = []
        for raw in jobs[: request.limit]:
            title = str(raw.get("title") or "")
            description = _ashby_description(raw)
            if not _matches(request.query, title, description):
                continue
            rows.append(
                build_posting(
                    provider=self.name,
                    source=board,
                    provider_job_id=raw.get("id"),
                    company=str(data.get("name") or board),
                    title=title,
                    location=_ashby_location(raw),
                    salary=_ashby_salary(raw),
                    employment_type=str(raw.get("employmentType") or ""),
                    job_url=str(raw.get("jobUrl") or raw.get("applyUrl") or ""),
                    posted_at=parse_datetime(raw.get("publishedAt")),
                    description=description,
                    industry=str(raw.get("department") or "") or None,
                )
            )
        return rows


def _ashby_description(raw: dict[str, Any]) -> str:
    parts = [
        str(raw.get("descriptionHtml") or ""),
        str(raw.get("descriptionPlain") or ""),
        str(raw.get("description") or ""),
    ]
    return " ".join(part for part in parts if part)


def _ashby_location(raw: dict[str, Any]) -> str | None:
    location = raw.get("location")
    if isinstance(location, dict):
        return str(location.get("name") or "") or None
    return str(location) if location else None


def _ashby_salary(raw: dict[str, Any]) -> str | None:
    compensation = raw.get("compensation")
    if isinstance(compensation, dict):
        return str(compensation.get("compensationTierSummary") or "") or None
    return None


def _matches(query: str | None, title: str, description: str) -> bool:
    if not query:
        return True
    needle = query.lower()
    return needle in title.lower() or needle in description.lower()
