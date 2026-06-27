from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from app.features.opportunity_discovery.providers.base import JobProvider, ProviderFetchRequest
from app.features.opportunity_discovery.providers.common import build_posting, get_text
from app.features.opportunity_discovery.schemas import JobProviderName, NormalizedJobPosting


class RSSProvider(JobProvider):
    name = JobProviderName.RSS

    def fetch(self, request: ProviderFetchRequest) -> list[NormalizedJobPosting]:
        url = request.source.strip()
        if not url:
            return []
        root = ElementTree.fromstring(get_text(url))
        rows: list[NormalizedJobPosting] = []
        for item in root.findall(".//item")[: request.limit]:
            title = _text(item, "title") or "Untitled role"
            description = _text(item, "description") or _text(item, "summary") or ""
            if not _matches(request.query, title, description):
                continue
            link = _text(item, "link") or url
            company = _text(item, "source") or _host_label(url)
            rows.append(
                build_posting(
                    provider=self.name,
                    source=url,
                    provider_job_id=_text(item, "guid") or link,
                    company=company,
                    title=title,
                    location=_text(item, "location"),
                    salary=None,
                    employment_type=None,
                    job_url=link,
                    posted_at=_parse_rss_date(_text(item, "pubDate")),
                    description=description,
                )
            )
        return rows


def _text(item: ElementTree.Element, name: str) -> str | None:
    child = item.find(name)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _parse_rss_date(value: str | None):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def _host_label(url: str) -> str:
    return url.split("//")[-1].split("/")[0] or "RSS feed"


def _matches(query: str | None, title: str, description: str) -> bool:
    if not query:
        return True
    needle = query.lower()
    return needle in title.lower() or needle in description.lower()
