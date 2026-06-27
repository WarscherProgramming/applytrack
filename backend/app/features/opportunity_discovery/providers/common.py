import html
import re
from datetime import UTC, datetime
from hashlib import sha1
from typing import Any

import httpx

from app.features.job_intelligence.service import JobIntelligenceService
from app.features.opportunity_discovery.schemas import (
    JobProviderName,
    NormalizedJobPosting,
    SkillTag,
    WorkMode,
)


def get_json(url: str) -> Any:
    response = httpx.get(url, timeout=15, follow_redirects=True)
    response.raise_for_status()
    return response.json()


def get_text(url: str) -> str:
    response = httpx.get(url, timeout=15, follow_redirects=True)
    response.raise_for_status()
    return response.text


def html_to_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def parse_datetime(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, int | float):
        # Greenhouse reports milliseconds; some feeds use seconds.
        seconds = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(seconds, tz=UTC)
    if isinstance(value, str):
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def infer_work_mode(*values: str | None) -> WorkMode:
    haystack = " ".join(value or "" for value in values).lower()
    if "remote" in haystack:
        return WorkMode.REMOTE
    if "hybrid" in haystack:
        return WorkMode.HYBRID
    if any(word in haystack for word in ("onsite", "on-site", "office")):
        return WorkMode.ONSITE
    return WorkMode.UNKNOWN


def normalize_skills(description: str) -> list[SkillTag]:
    return [
        SkillTag(name=skill.name, category=skill.category)
        for skill in JobIntelligenceService.extract_skills(description)
    ]


def posting_id(provider: JobProviderName, source: str, provider_job_id: object, url: str) -> str:
    stable = f"{provider}:{source}:{provider_job_id or url}"
    return sha1(stable.encode("utf-8")).hexdigest()


def build_posting(
    *,
    provider: JobProviderName,
    source: str,
    provider_job_id: object,
    company: str,
    title: str,
    location: str | None,
    salary: str | None,
    employment_type: str | None,
    job_url: str,
    posted_at: datetime | None,
    description: str,
    industry: str | None = None,
) -> NormalizedJobPosting:
    clean_description = html_to_text(description)
    return NormalizedJobPosting(
        id=posting_id(provider, source, provider_job_id, job_url),
        provider=provider,
        provider_job_id=str(provider_job_id) if provider_job_id is not None else None,
        company=company.strip() or "Unknown company",
        title=title.strip() or "Untitled role",
        location=location.strip() if location else None,
        salary=salary.strip() if salary else None,
        employment_type=employment_type.strip() if employment_type else None,
        work_mode=infer_work_mode(location, employment_type, clean_description),
        job_url=job_url,
        posted_at=posted_at,
        description=clean_description,
        skills=normalize_skills(clean_description),
        industry=industry,
    )
