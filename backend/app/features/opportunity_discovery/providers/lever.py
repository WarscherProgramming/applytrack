from typing import Any

from app.features.opportunity_discovery.providers.base import JobProvider, ProviderFetchRequest
from app.features.opportunity_discovery.providers.common import (
    build_posting,
    get_json,
    parse_datetime,
)
from app.features.opportunity_discovery.schemas import JobProviderName, NormalizedJobPosting


class LeverProvider(JobProvider):
    name = JobProviderName.LEVER

    def fetch(self, request: ProviderFetchRequest) -> list[NormalizedJobPosting]:
        company = request.source.strip().strip("/")
        if not company:
            return []
        data = get_json(f"https://api.lever.co/v0/postings/{company}?mode=json")
        rows: list[NormalizedJobPosting] = []
        for raw in data[: request.limit]:
            title = str(raw.get("text") or "")
            description = _lever_description(raw)
            if not _matches(request.query, title, description):
                continue
            rows.append(
                build_posting(
                    provider=self.name,
                    source=company,
                    provider_job_id=raw.get("id"),
                    company=company,
                    title=title,
                    location=_lever_location(raw),
                    salary=_lever_salary(raw),
                    employment_type=str(raw.get("commitment") or ""),
                    job_url=str(raw.get("hostedUrl") or raw.get("applyUrl") or ""),
                    posted_at=parse_datetime(raw.get("createdAt")),
                    description=description,
                    industry=str(raw.get("team") or "") or None,
                )
            )
        return rows


def _lever_description(raw: dict[str, Any]) -> str:
    parts = [str(raw.get("description") or ""), str(raw.get("descriptionPlain") or "")]
    for list_name in ("lists", "content"):
        values = raw.get(list_name) or []
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict):
                    parts.append(str(item.get("content") or item.get("text") or ""))
    return " ".join(part for part in parts if part)


def _lever_location(raw: dict[str, Any]) -> str | None:
    categories = raw.get("categories") or {}
    if isinstance(categories, dict):
        location = categories.get("location")
        if location:
            return str(location)
    return None


def _lever_salary(raw: dict[str, Any]) -> str | None:
    salary = raw.get("salaryRange")
    if isinstance(salary, dict):
        minimum = salary.get("min")
        maximum = salary.get("max")
        currency = salary.get("currency") or ""
        if minimum and maximum:
            return f"{currency} {minimum}-{maximum}".strip()
    return None


def _matches(query: str | None, title: str, description: str) -> bool:
    if not query:
        return True
    needle = query.lower()
    return needle in title.lower() or needle in description.lower()
