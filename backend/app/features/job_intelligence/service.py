import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.ai.errors import AIError
from app.core.config import settings
from app.features.job_intelligence.repository import JobIntelligenceRepository
from app.features.job_intelligence.schemas import (
    CategoryBreakdown,
    DistributionItem,
    JobDescriptionSource,
    JobIntelligenceAI,
    JobIntelligenceAIResult,
    JobIntelligenceFilters,
    JobIntelligenceResponse,
    MissingSkill,
    SkillSignal,
    TrendPoint,
)
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resume_match.text_extraction import extract_text
from app.features.resumes.model import Resume
from app.features.resumes.service import ResumeService

logger = logging.getLogger(__name__)

FEATURE = "job_intelligence"
PROMPT_TEMPLATE = "job_intelligence.v1"

TAXONOMY: dict[str, dict[str, tuple[str, ...]]] = {
    "Programming Languages": {
        "Python": (r"\bpython\b",),
        "Java": (r"\bjava\b",),
        "C#": (r"(?<!\w)c#(?!\w)|\bc sharp\b|\.net c#",),
        "JavaScript": (r"\bjavascript\b|\bjs\b",),
        "TypeScript": (r"\btypescript\b|\bts\b",),
        "Go": (r"\bgolang\b|\bgo\b",),
        "Rust": (r"\brust\b",),
        "Ruby": (r"\bruby\b",),
        "PHP": (r"\bphp\b",),
        "Swift": (r"\bswift\b",),
        "Kotlin": (r"\bkotlin\b",),
        "SQL": (r"\bsql\b",),
    },
    "Frameworks": {
        "React": (r"\breact(?:\.js)?\b",),
        "Angular": (r"\bangular\b",),
        "Vue": (r"\bvue(?:\.js)?\b",),
        "Django": (r"\bdjango\b",),
        "FastAPI": (r"\bfastapi\b",),
        "Flask": (r"\bflask\b",),
        "Spring": (r"\bspring(?: boot)?\b",),
        "ASP.NET": (r"\basp\.?net\b",),
        "Node.js": (r"\bnode(?:\.js)?\b",),
        "Express": (r"\bexpress(?:\.js)?\b",),
        "Next.js": (r"\bnext(?:\.js)?\b",),
    },
    "Cloud Platforms": {
        "AWS": (r"\baws\b|amazon web services",),
        "Azure": (r"\bazure\b",),
        "GCP": (r"\bgcp\b|google cloud",),
    },
    "Databases": {
        "PostgreSQL": (r"\bpostgres(?:ql)?\b",),
        "MySQL": (r"\bmysql\b",),
        "SQL Server": (r"\bsql server\b|mssql",),
        "MongoDB": (r"\bmongodb\b",),
        "Redis": (r"\bredis\b",),
        "Elasticsearch": (r"\belasticsearch\b|elastic search",),
        "DynamoDB": (r"\bdynamodb\b",),
    },
    "DevOps": {
        "Docker": (r"\bdocker\b",),
        "Kubernetes": (r"\bkubernetes\b|\bk8s\b",),
        "Terraform": (r"\bterraform\b",),
        "GitHub Actions": (r"github actions",),
        "Jenkins": (r"\bjenkins\b",),
        "GitLab CI": (r"gitlab ci",),
        "Ansible": (r"\bansible\b",),
    },
    "Concepts": {
        "REST APIs": (r"\brest(?:ful)?\b|\brest apis?\b",),
        "GraphQL": (r"\bgraphql\b",),
        "Microservices": (r"\bmicroservices?\b",),
        "CI/CD": (r"\bci/cd\b|continuous integration|continuous delivery",),
        "Distributed Systems": (r"\bdistributed systems?\b",),
        "Testing": (r"\btesting\b|\bunit tests?\b|\bintegration tests?\b|pytest|jest",),
        "Security": (r"\bsecurity\b|oauth|sso|iam|zero trust",),
        "System Design": (r"\bsystem design\b",),
        "Event-Driven Architecture": (r"event[- ]driven|message queues?|pub/sub",),
    },
    "Soft Skills": {
        "Communication": (r"\bcommunication\b|communicat(?:e|ion|ing)",),
        "Leadership": (r"\bleadership\b|\blead teams?\b|\btech lead\b",),
        "Mentoring": (r"\bmentor(?:ing)?\b|coach(?:ing)?",),
        "Collaboration": (r"\bcollaboration\b|cross-functional|teamwork",),
        "Problem Solving": (r"problem[- ]solving|solve complex",),
        "Ownership": (r"\bownership\b|accountab",),
    },
}

ALIASES: dict[str, str] = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "k8s": "Kubernetes",
    "golang": "Go",
    "google cloud": "GCP",
    "amazon web services": "AWS",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "ci cd": "CI/CD",
    "cicd": "CI/CD",
    "asp net": "ASP.NET",
    "node": "Node.js",
    "nodejs": "Node.js",
}


@dataclass(frozen=True)
class ExtractedSkill:
    name: str
    category: str


@dataclass(frozen=True)
class JobPosting:
    id: str
    source: str
    created_at: datetime
    text: str
    company: str | None = None
    industry: str | None = None
    role: str | None = None
    resume_id: UUID | None = None
    application_id: UUID | None = None


class JobIntelligenceService:
    """
    Builds structured job-market intelligence from saved job descriptions.

    Pipeline: extraction -> normalization -> analytics -> AI interpretation.
    The deterministic report is complete without AI; AI only explains the
    computed analytics.
    """

    def __init__(self, db: Session, *, ai_client: AIClient | None = None) -> None:
        self.db = db
        self.repo = JobIntelligenceRepository(db)
        self.resume_service = ResumeService(db)
        self._injected_client = ai_client

    def build_report(
        self,
        *,
        date_from: str | date | None = None,
        date_to: str | date | None = None,
        industry: str | None = None,
        company: str | None = None,
        role: str | None = None,
    ) -> JobIntelligenceResponse:
        filters = JobIntelligenceFilters(
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            industry=_clean_filter(industry),
            company=_clean_filter(company),
            role=_clean_filter(role),
        )
        all_postings = self._collect_postings()
        postings = self._filter_postings(all_postings, filters)
        resume_skills = self._resume_skills(self.repo.list_resumes())
        resume_match_gaps = self._resume_match_gap_counts(self.repo.list_resume_match_analyses())

        skill_signals = self._skill_signals(postings)
        category_breakdown = self._category_breakdown(skill_signals)
        missing_skills = self._missing_skills(skill_signals, resume_skills, resume_match_gaps)
        industry_breakdown = _distribution([p.industry or "Unknown" for p in postings])
        company_breakdown = _distribution([p.company or "Unknown" for p in postings])
        role_breakdown = _distribution([p.role or "Unknown" for p in postings])

        facts = {
            "filters": filters.model_dump(mode="json"),
            "job_description_count": len(postings),
            "resume_skill_count": len(resume_skills),
            "top_skills": [item.model_dump(mode="json") for item in skill_signals[:15]],
            "category_breakdown": [
                item.model_dump(mode="json") for item in category_breakdown
            ],
            "missing_skills": [item.model_dump(mode="json") for item in missing_skills[:10]],
            "industry_breakdown": [
                item.model_dump(mode="json") for item in industry_breakdown[:8]
            ],
            "company_breakdown": [
                item.model_dump(mode="json") for item in company_breakdown[:8]
            ],
            "role_breakdown": [item.model_dump(mode="json") for item in role_breakdown[:8]],
        }

        return JobIntelligenceResponse(
            generated_at=datetime.now(UTC),
            filters=filters,
            job_description_count=len(postings),
            source_count=len(all_postings),
            resume_skill_count=len(resume_skills),
            sources=[
                JobDescriptionSource(
                    id=posting.id,
                    source=posting.source,
                    created_at=posting.created_at,
                    company=posting.company,
                    industry=posting.industry,
                    role=posting.role,
                    resume_id=posting.resume_id,
                    application_id=posting.application_id,
                )
                for posting in postings[:100]
            ],
            skill_signals=skill_signals,
            category_breakdown=category_breakdown,
            missing_skills=missing_skills,
            industry_breakdown=industry_breakdown,
            company_breakdown=company_breakdown,
            role_breakdown=role_breakdown,
            ai_interpretation=self._ai_interpretation(facts),
        )

    @staticmethod
    def extract_skills(text: str) -> list[ExtractedSkill]:
        found: list[ExtractedSkill] = []
        for category, skills in TAXONOMY.items():
            for canonical, patterns in skills.items():
                if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
                    found.append(ExtractedSkill(name=canonical, category=category))
        return found

    @staticmethod
    def normalize_skill(value: str) -> ExtractedSkill | None:
        cleaned = re.sub(r"[^a-zA-Z0-9+#.]+", " ", value).strip().lower()
        if not cleaned:
            return None
        canonical_hint = ALIASES.get(cleaned)
        for category, skills in TAXONOMY.items():
            for canonical in skills:
                if canonical_hint == canonical or cleaned == canonical.lower():
                    return ExtractedSkill(name=canonical, category=category)
        for category, skills in TAXONOMY.items():
            for canonical, patterns in skills.items():
                if any(re.fullmatch(pattern, cleaned, flags=re.IGNORECASE) for pattern in patterns):
                    return ExtractedSkill(name=canonical, category=category)
        return None

    def _collect_postings(self) -> list[JobPosting]:
        applications = {app.id: app for app in self.repo.list_applications()}
        companies = {company.id: company for company in self.repo.list_companies()}
        postings: list[JobPosting] = []

        for analysis in self.repo.list_resume_match_analyses():
            postings.append(
                JobPosting(
                    id=f"resume-match-{analysis.id}",
                    source="resume_match",
                    created_at=analysis.created_at,
                    text=analysis.job_description,
                    role=None,
                    resume_id=analysis.resume_id,
                )
            )

        for package in self.repo.list_interview_prep_packages():
            app = applications.get(package.application_id) if package.application_id else None
            company = companies.get(app.company_id) if app else None
            postings.append(
                JobPosting(
                    id=f"interview-prep-{package.id}",
                    source="interview_prep",
                    created_at=package.created_at,
                    text=package.job_description,
                    company=package.company_name or (company.name if company else None),
                    industry=company.industry if company else None,
                    role=package.job_title or (app.job_title if app else None),
                    resume_id=package.resume_id,
                    application_id=package.application_id,
                )
            )

        return [posting for posting in postings if posting.text and posting.text.strip()]

    @staticmethod
    def _filter_postings(
        postings: list[JobPosting], filters: JobIntelligenceFilters
    ) -> list[JobPosting]:
        rows = []
        for posting in postings:
            created = posting.created_at.date()
            if filters.date_from and created < filters.date_from:
                continue
            if filters.date_to and created > filters.date_to:
                continue
            if filters.industry and filters.industry.lower() not in (
                posting.industry or ""
            ).lower():
                continue
            if filters.company and filters.company.lower() not in (
                posting.company or ""
            ).lower():
                continue
            if filters.role and filters.role.lower() not in (posting.role or "").lower():
                continue
            rows.append(posting)
        return rows

    def _resume_skills(self, resumes: list[Resume]) -> set[str]:
        skills: set[str] = set()
        for resume in resumes:
            try:
                downloaded = self.resume_service.download(resume.id)
                text = extract_text(downloaded.record.file_name, downloaded.content)
            except Exception as exc:  # pragma: no cover - defensive against corrupt uploads
                logger.info("Skipping resume skill extraction id=%s: %s", resume.id, exc)
                continue
            skills.update(skill.name for skill in self.extract_skills(text))
        return skills

    @classmethod
    def _resume_match_gap_counts(
        cls, analyses: list[ResumeMatchAnalysis]
    ) -> Counter[str]:
        counts: Counter[str] = Counter()
        for analysis in analyses:
            for raw in (analysis.result or {}).get("missing_skills", []):
                if not isinstance(raw, str):
                    continue
                normalized = cls.normalize_skill(raw)
                if normalized:
                    counts[normalized.name] += 1
        return counts

    def _skill_signals(self, postings: list[JobPosting]) -> list[SkillSignal]:
        by_skill: dict[str, list[JobPosting]] = defaultdict(list)
        category_by_skill: dict[str, str] = {}
        for posting in postings:
            for skill in self.extract_skills(posting.text):
                by_skill[skill.name].append(posting)
                category_by_skill[skill.name] = skill.category

        total = len(postings)
        signals: list[SkillSignal] = []
        for name, skill_postings in by_skill.items():
            periods = Counter(_period(p.created_at) for p in skill_postings)
            trend_points = [
                TrendPoint(period=period, count=count)
                for period, count in sorted(periods.items())
            ]
            signals.append(
                SkillSignal(
                    name=name,
                    category=category_by_skill[name],
                    frequency=len(skill_postings),
                    percentage=_percent(len(skill_postings), total),
                    trend_delta=_trend_delta(trend_points),
                    trend=trend_points,
                    industry_distribution=_distribution(
                        [p.industry or "Unknown" for p in skill_postings]
                    ),
                    company_distribution=_distribution(
                        [p.company or "Unknown" for p in skill_postings]
                    ),
                    role_distribution=_distribution(
                        [p.role or "Unknown" for p in skill_postings]
                    ),
                )
            )
        signals.sort(
            key=lambda item: (item.frequency, item.trend_delta, item.name),
            reverse=True,
        )
        return signals

    @staticmethod
    def _category_breakdown(skill_signals: list[SkillSignal]) -> list[CategoryBreakdown]:
        grouped: dict[str, list[SkillSignal]] = defaultdict(list)
        for signal in skill_signals:
            grouped[signal.category].append(signal)
        rows = [
            CategoryBreakdown(
                category=category,
                count=sum(skill.frequency for skill in skills),
                skills=skills[:10],
            )
            for category, skills in grouped.items()
        ]
        rows.sort(key=lambda item: item.count, reverse=True)
        return rows

    @staticmethod
    def _missing_skills(
        skill_signals: list[SkillSignal],
        resume_skills: set[str],
        resume_match_gaps: Counter[str],
    ) -> list[MissingSkill]:
        rows = []
        for signal in skill_signals:
            if signal.name in resume_skills:
                continue
            reason = "Present in job market but absent from extracted resume skills"
            gap_count = resume_match_gaps[signal.name]
            if gap_count:
                reason += f"; also flagged by Resume Match {gap_count} time(s)"
            rows.append(
                MissingSkill(
                    name=signal.name,
                    category=signal.category,
                    market_frequency=signal.frequency,
                    market_percentage=signal.percentage,
                    resume_match_gap_count=gap_count,
                    reason=reason,
                )
            )
        rows.sort(
            key=lambda item: (
                item.resume_match_gap_count,
                item.market_frequency,
                item.name,
            ),
            reverse=True,
        )
        return rows

    def _ai_interpretation(self, facts: dict) -> JobIntelligenceAI:
        fallback = self._fallback_interpretation(facts)
        if facts["job_description_count"] == 0:
            return fallback
        try:
            prompt = render_template(
                PROMPT_TEMPLATE,
                {"job_intelligence_json": json.dumps(facts, sort_keys=True)},
            )
            client = self._resolve_client(fallback)
            structured = client.generate_structured(
                GenerationRequest(
                    system=prompt.system,
                    prompt=prompt.user,
                    temperature=0.2,
                ),
                JobIntelligenceAIResult,
                db=self.db,
                feature=FEATURE,
            )
            result = structured.data
            return JobIntelligenceAI(
                available=True,
                provider=structured.result.provider,
                model=structured.result.model,
                executive_summary=result.executive_summary,
                top_learning_priorities=result.top_learning_priorities,
                emerging_technologies=result.emerging_technologies,
                resume_recommendations=result.resume_recommendations,
                skill_investment_suggestions=result.skill_investment_suggestions,
                career_direction_suggestions=result.career_direction_suggestions,
                caveats=result.caveats,
            )
        except AIError as exc:
            logger.warning("Job Intelligence AI interpretation unavailable: %s", exc)
            return fallback.model_copy(
                update={
                    "caveats": [
                        *fallback.caveats,
                        "AI interpretation unavailable; showing deterministic guidance.",
                    ]
                }
            )

    def _resolve_client(self, fallback: JobIntelligenceAI) -> AIClient:
        if self._injected_client is not None:
            return self._injected_client
        if settings.ai_active_provider == "mock":
            payload = JobIntelligenceAIResult(
                executive_summary=fallback.executive_summary,
                top_learning_priorities=fallback.top_learning_priorities,
                emerging_technologies=fallback.emerging_technologies,
                resume_recommendations=fallback.resume_recommendations,
                skill_investment_suggestions=fallback.skill_investment_suggestions,
                career_direction_suggestions=fallback.career_direction_suggestions,
                caveats=fallback.caveats,
            )
            return AIClient(
                MockProvider(default_response=payload.model_dump_json()),
                default_model=settings.AI_MODEL,
            )
        return get_ai_client()

    @staticmethod
    def _fallback_interpretation(facts: dict) -> JobIntelligenceAI:
        top_skills = facts["top_skills"]
        missing = facts["missing_skills"]
        caveats: list[str] = []
        if facts["job_description_count"] < 3:
            caveats.append("Small sample size; treat the ranking as directional.")
        if not top_skills:
            caveats.append("No recognized skills were extracted from saved job descriptions.")

        priorities = [
            f"Study {item['name']} ({item['market_frequency']} postings)"
            for item in missing[:5]
        ]
        if not priorities and top_skills:
            priorities = [f"Keep sharpening {top_skills[0]['name']}"]

        emerging = [
            item["name"] for item in top_skills if item.get("trend_delta", 0) > 0
        ][:5]
        resume_recs = [
            f"Add truthful evidence for {item['name']} if you have it."
            for item in missing[:5]
        ]

        return JobIntelligenceAI(
            available=False,
            executive_summary=(
                f"Analyzed {facts['job_description_count']} saved job descriptions "
                "and built deterministic skill-market signals."
            ),
            top_learning_priorities=priorities,
            emerging_technologies=emerging,
            resume_recommendations=resume_recs,
            skill_investment_suggestions=priorities,
            career_direction_suggestions=[
                "Use the highest-frequency skills to guide target roles and project work."
            ]
            if facts["job_description_count"]
            else ["Save job descriptions through Resume Match or Interview Prep first."],
            caveats=caveats,
        )


def _parse_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _clean_filter(value: str | None) -> str | None:
    stripped = value.strip() if value else None
    return stripped or None


def _period(value: datetime) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _trend_delta(points: list[TrendPoint]) -> int:
    if not points:
        return 0
    if len(points) == 1:
        return points[0].count
    return points[-1].count - points[-2].count


def _distribution(values: list[str], limit: int = 8) -> list[DistributionItem]:
    counts = Counter(values)
    total = sum(counts.values())
    return [
        DistributionItem(name=name, count=count, percentage=_percent(count, total))
        for name, count in counts.most_common(limit)
    ]


def _percent(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator * 100, 2)
