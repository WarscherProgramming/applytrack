from __future__ import annotations

import json
import logging
import re
from collections import Counter
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.ai.errors import AIError
from app.core.config import settings
from app.features.applications.model import ApplicationStatus
from app.features.job_intelligence.service import JobIntelligenceService
from app.features.opportunity_discovery.providers import (
    AshbyProvider,
    GreenhouseProvider,
    JobProvider,
    LeverProvider,
    ProviderFetchRequest,
    RSSProvider,
)
from app.features.opportunity_discovery.repository import OpportunityDiscoveryRepository
from app.features.opportunity_discovery.schemas import (
    DistributionSummary,
    JobProviderName,
    NormalizedJobPosting,
    OpportunityAIExplanation,
    OpportunityAIExplanationResult,
    OpportunitySearchRequest,
    OpportunitySearchResponse,
    ProviderIssue,
    SaveOpportunityRequest,
    SaveOpportunityResponse,
    ScoredOpportunity,
    SkillTagSummary,
)
from app.features.opportunity_discovery.scoring import (
    OpportunityScoringEngine,
    ScoringContext,
    build_resume_profiles,
)
from app.features.resume_match.text_extraction import extract_text
from app.features.resumes.service import ResumeService

logger = logging.getLogger(__name__)

FEATURE = "opportunity_discovery"
PROMPT_TEMPLATE = "opportunity_discovery.v1"


class OpportunityDiscoveryService:
    """Orchestrates provider discovery, scoring, and save-to-pipeline actions."""

    def __init__(
        self,
        db: Session,
        *,
        providers: dict[JobProviderName, JobProvider] | None = None,
        ai_client: AIClient | None = None,
    ) -> None:
        self.db = db
        self.repo = OpportunityDiscoveryRepository(db)
        self.resume_service = ResumeService(db)
        self.scoring = OpportunityScoringEngine()
        self.providers = providers or {
            JobProviderName.GREENHOUSE: GreenhouseProvider(),
            JobProviderName.LEVER: LeverProvider(),
            JobProviderName.ASHBY: AshbyProvider(),
            JobProviderName.RSS: RSSProvider(),
        }
        self._injected_client = ai_client

    def search(self, request: OpportunitySearchRequest) -> OpportunitySearchResponse:
        postings, issues = self._fetch_postings(request)
        filtered = self._filter_postings(postings, request)[: request.limit]
        context = self._scoring_context(request)
        items = [
            ScoredOpportunity(
                posting=posting,
                score=(score := self.scoring.score(posting, context)),
                ai_explanation=self._ai_explanation(posting, score),
            )
            for posting in filtered
        ]
        items.sort(key=lambda item: item.score.overall_match_percent, reverse=True)
        return OpportunitySearchResponse(
            items=items,
            total=len(items),
            provider_issues=issues,
            top_technologies=_top_technologies([item.posting for item in items]),
            top_industries=_top_distributions(
                [item.posting.industry or "Unknown" for item in items]
            ),
            top_locations=_top_distributions(
                [item.posting.location or "Unknown" for item in items]
            ),
        )

    def save(self, request: SaveOpportunityRequest) -> SaveOpportunityResponse:
        posting = request.posting
        company = self.repo.get_company_by_name(posting.company)
        company_created = False
        if company is None:
            company = self.repo.create_company(
                {
                    "name": posting.company,
                    "website": _company_site(posting.job_url),
                    "industry": posting.industry,
                    "location": posting.location,
                    "notes": "Created from Opportunity Discovery.",
                }
            )
            company_created = True

        if request.resume_id is not None:
            self.repo.get_resume(request.resume_id)
        if request.cover_letter_id is not None:
            self.repo.get_cover_letter(request.cover_letter_id)

        application = self.repo.create_application(
            {
                "company_id": company.id,
                "job_title": posting.title,
                "job_link": posting.job_url,
                "location": posting.location,
                "salary_range": posting.salary,
                "status": ApplicationStatus.DRAFT.value,
                "source": f"Opportunity Discovery: {posting.provider.value}",
                "notes": _application_notes(posting),
                "resume_id": request.resume_id,
                "cover_letter_id": request.cover_letter_id,
            }
        )
        logger.info(
            "Saved opportunity provider=%s company=%r application_id=%s",
            posting.provider.value,
            posting.company,
            application.id,
        )
        return SaveOpportunityResponse(application=application, company_created=company_created)

    def _fetch_postings(
        self, request: OpportunitySearchRequest
    ) -> tuple[list[NormalizedJobPosting], list[ProviderIssue]]:
        postings: list[NormalizedJobPosting] = []
        issues: list[ProviderIssue] = []
        for provider_name, source in _provider_sources(request):
            provider = self.providers.get(provider_name)
            if provider is None:
                issues.append(
                    ProviderIssue(
                        provider=provider_name,
                        source=source,
                        message="Provider is not configured.",
                    )
                )
                continue
            try:
                postings.extend(
                    provider.fetch(
                        ProviderFetchRequest(
                            source=source,
                            query=request.query,
                            limit=request.limit,
                        )
                    )
                )
            except (httpx.HTTPError, ValueError) as exc:
                issues.append(
                    ProviderIssue(provider=provider_name, source=source, message=str(exc))
                )
        return _dedupe_postings(postings), issues

    def _filter_postings(
        self, postings: list[NormalizedJobPosting], request: OpportunitySearchRequest
    ) -> list[NormalizedJobPosting]:
        rows = []
        technology_filters = {
            skill.name
            for value in request.technologies
            if (skill := JobIntelligenceService.normalize_skill(value)) is not None
        }
        query = (request.query or "").strip().lower()
        location = (request.location or "").strip().lower()
        for posting in postings:
            if request.remote and request.remote != posting.work_mode:
                continue
            if location and location not in (posting.location or "").lower():
                continue
            if request.min_salary is not None and not _salary_meets(
                posting.salary, request.min_salary
            ):
                continue
            posting_skills = {skill.name for skill in posting.skills}
            if technology_filters and not technology_filters <= posting_skills:
                continue
            haystack = f"{posting.title} {posting.company} {posting.description}".lower()
            if query and query not in haystack:
                continue
            rows.append(posting)
        return rows

    def _scoring_context(self, request: OpportunitySearchRequest) -> ScoringContext:
        resumes = self.repo.list_resumes()
        return ScoringContext(
            resume_profiles=build_resume_profiles(resumes, self._resume_skills(resumes)),
            selected_resume_id=request.resume_id,
            cover_letters=self.repo.list_cover_letters(),
            applications=self.repo.list_applications(),
            companies=self.repo.list_companies(),
            preferred_location=request.preferred_location,
            preferred_job_type=request.preferred_job_type,
            preferred_industry=request.preferred_industry,
        )

    def _resume_skills(self, resumes) -> dict[UUID, set[str]]:
        rows: dict[UUID, set[str]] = {}
        for resume in resumes:
            try:
                downloaded = self.resume_service.download(resume.id)
                text = extract_text(downloaded.record.file_name, downloaded.content)
            except Exception as exc:  # pragma: no cover - defensive against corrupt uploads
                logger.info("Skipping resume in opportunity scoring id=%s: %s", resume.id, exc)
                continue
            rows[resume.id] = {
                skill.name for skill in JobIntelligenceService.extract_skills(text)
            }
        return rows

    def _ai_explanation(
        self, posting: NormalizedJobPosting, score
    ) -> OpportunityAIExplanation:
        fallback = _fallback_explanation(posting, score)
        try:
            prompt = render_template(
                PROMPT_TEMPLATE,
                {
                    "opportunity_score_json": json.dumps(
                        {
                            "posting": posting.model_dump(mode="json"),
                            "score": score.model_dump(mode="json"),
                        },
                        sort_keys=True,
                    )
                },
            )
            client = self._resolve_client(fallback)
            structured = client.generate_structured(
                GenerationRequest(system=prompt.system, prompt=prompt.user, temperature=0.2),
                OpportunityAIExplanationResult,
                db=self.db,
                feature=FEATURE,
            )
            result = structured.data
            return OpportunityAIExplanation(
                available=True,
                provider=structured.result.provider,
                model=structured.result.model,
                summary=result.summary,
                score_explanation=result.score_explanation,
                next_steps=result.next_steps,
                cautions=result.cautions,
            )
        except AIError as exc:
            logger.warning("Opportunity Discovery AI explanation unavailable: %s", exc)
            return fallback.model_copy(
                update={
                    "cautions": [
                        *fallback.cautions,
                        "AI explanation unavailable; showing deterministic scoring rationale.",
                    ]
                }
            )

    def _resolve_client(self, fallback: OpportunityAIExplanation) -> AIClient:
        if self._injected_client is not None:
            return self._injected_client
        if settings.ai_active_provider == "mock":
            payload = OpportunityAIExplanationResult(
                summary=fallback.summary,
                score_explanation=fallback.score_explanation,
                next_steps=fallback.next_steps,
                cautions=fallback.cautions,
            )
            return AIClient(
                MockProvider(default_response=payload.model_dump_json()),
                default_model=settings.AI_MODEL,
            )
        return get_ai_client()


def _provider_sources(request: OpportunitySearchRequest) -> list[tuple[JobProviderName, str]]:
    requested = set(request.providers)
    rows: list[tuple[JobProviderName, str]] = []
    if not requested or JobProviderName.GREENHOUSE in requested:
        rows.extend((JobProviderName.GREENHOUSE, source) for source in request.greenhouse_boards)
    if not requested or JobProviderName.LEVER in requested:
        rows.extend((JobProviderName.LEVER, source) for source in request.lever_companies)
    if not requested or JobProviderName.ASHBY in requested:
        rows.extend((JobProviderName.ASHBY, source) for source in request.ashby_boards)
    if not requested or JobProviderName.RSS in requested:
        rows.extend((JobProviderName.RSS, source) for source in request.rss_feeds)
    return [(provider, source.strip()) for provider, source in rows if source.strip()]


def _dedupe_postings(postings: list[NormalizedJobPosting]) -> list[NormalizedJobPosting]:
    seen: set[str] = set()
    rows = []
    for posting in postings:
        key = posting.job_url or posting.id
        if key in seen:
            continue
        seen.add(key)
        rows.append(posting)
    return rows


def _salary_meets(salary: str | None, minimum: int) -> bool:
    if salary is None:
        return False
    numbers = [int(value.replace(",", "")) for value in re.findall(r"\d[\d,]*", salary)]
    if not numbers:
        return False
    return max(numbers) >= minimum


def _top_technologies(postings: list[NormalizedJobPosting]) -> list[SkillTagSummary]:
    categories: dict[str, str] = {}
    counts: Counter[str] = Counter()
    for posting in postings:
        for skill in posting.skills:
            counts[skill.name] += 1
            categories[skill.name] = skill.category
    return [
        SkillTagSummary(name=name, category=categories[name], count=count)
        for name, count in counts.most_common(10)
    ]


def _top_distributions(values: list[str]) -> list[DistributionSummary]:
    return [
        DistributionSummary(name=name, count=count)
        for name, count in Counter(values).most_common(10)
    ]


def _fallback_explanation(posting, score) -> OpportunityAIExplanation:
    return OpportunityAIExplanation(
        available=False,
        summary=(
            f"{posting.title} at {posting.company} scored "
            f"{score.overall_match_percent}% from deterministic ApplyTrack signals."
        ),
        score_explanation=" ".join(score.reasoning[:3]),
        next_steps=[
            "Review missing skills before applying.",
            "Open Quick Resume Match if you want a deeper resume-specific review.",
        ],
        cautions=[],
    )


def _company_site(job_url: str) -> str | None:
    if not job_url.startswith(("http://", "https://")):
        return None
    host = job_url.split("//", 1)[1].split("/", 1)[0]
    return f"https://{host}" if host else None


def _application_notes(posting: NormalizedJobPosting) -> str:
    skills = ", ".join(skill.name for skill in posting.skills[:10]) or "No extracted skills"
    return (
        "Imported from Opportunity Discovery.\n"
        f"Provider: {posting.provider.value}\n"
        f"Posting URL: {posting.job_url}\n"
        f"Extracted skills: {skills}"
    )
