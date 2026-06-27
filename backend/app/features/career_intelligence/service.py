import json
import logging
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from statistics import mean

from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.ai.errors import AIError
from app.core.config import settings
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.career_intelligence.repository import CareerIntelligenceRepository
from app.features.career_intelligence.schemas import (
    AIRecommendation,
    AIRecommendationResult,
    AIRecommendations,
    ApplicationMetrics,
    CareerIntelligenceResponse,
    CompanyInsights,
    ComparisonMetric,
    CountInsight,
    DocumentInsights,
    DocumentPerformance,
    IntelligenceFilters,
    InterviewIntelligence,
    PeriodComparison,
    RateMetric,
    SegmentInsight,
    SkillIntelligence,
    TrendInsight,
)
from app.features.companies.model import Company
from app.features.cover_letters.model import CoverLetter
from app.features.gmail.models import EmailMessage
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.interviews.model import Interview
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.model import Resume

logger = logging.getLogger(__name__)

FEATURE = "career_intelligence"
PROMPT_TEMPLATE = "career_intelligence.v1"

TERMINAL_STATUSES = {
    ApplicationStatus.ACCEPTED.value,
    ApplicationStatus.REJECTED.value,
    ApplicationStatus.WITHDRAWN.value,
    ApplicationStatus.GHOSTED.value,
}
RESPONSE_STATUSES = {
    ApplicationStatus.ASSESSMENT.value,
    ApplicationStatus.PHONE_SCREEN.value,
    ApplicationStatus.INTERVIEW.value,
    ApplicationStatus.FINAL_INTERVIEW.value,
    ApplicationStatus.OFFER.value,
    ApplicationStatus.ACCEPTED.value,
    ApplicationStatus.REJECTED.value,
}
INTERVIEW_STATUSES = {
    ApplicationStatus.PHONE_SCREEN.value,
    ApplicationStatus.INTERVIEW.value,
    ApplicationStatus.FINAL_INTERVIEW.value,
    ApplicationStatus.OFFER.value,
    ApplicationStatus.ACCEPTED.value,
}
OFFER_STATUSES = {ApplicationStatus.OFFER.value, ApplicationStatus.ACCEPTED.value}

SKILL_PATTERNS: dict[str, str] = {
    "Python": r"\bpython\b",
    "JavaScript": r"\bjavascript\b|\bjs\b",
    "TypeScript": r"\btypescript\b|\bts\b",
    "React": r"\breact\b",
    "Node.js": r"\bnode(?:\.js)?\b",
    "FastAPI": r"\bfastapi\b",
    "Django": r"\bdjango\b",
    "Flask": r"\bflask\b",
    "SQL": r"\bsql\b",
    "PostgreSQL": r"\bpostgres(?:ql)?\b",
    "MySQL": r"\bmysql\b",
    "MongoDB": r"\bmongodb\b",
    "Redis": r"\bredis\b",
    "AWS": r"\baws\b|amazon web services",
    "Azure": r"\bazure\b",
    "Google Cloud": r"\bgcp\b|google cloud",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Terraform": r"\bterraform\b",
    "CI/CD": r"\bci/cd\b|continuous integration|continuous delivery",
    "GraphQL": r"\bgraphql\b",
    "REST": r"\brest(?:ful)?\b",
    "Microservices": r"\bmicroservices?\b",
    "System Design": r"\bsystem design\b",
    "Machine Learning": r"\bmachine learning\b|\bml\b",
    "AI": r"\bai\b|artificial intelligence",
    "Data Engineering": r"\bdata engineering\b",
    "Spark": r"\bspark\b|pyspark",
    "Kafka": r"\bkafka\b",
    "Security": r"\bsecurity\b|oauth|sso|iam",
}
TECHNOLOGY_SKILLS = {
    "React",
    "TypeScript",
    "Python",
    "FastAPI",
    "PostgreSQL",
    "AWS",
    "Azure",
    "Google Cloud",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Kafka",
    "Spark",
    "Machine Learning",
    "AI",
}
CERTIFICATION_PATTERNS: dict[str, str] = {
    "AWS Certified": r"\baws certified\b|\baws certification\b",
    "Azure Certification": r"\bazure certified\b|\bazure certification\b",
    "Google Cloud Certification": r"\bgcp certified\b|google cloud certified",
    "PMP": r"\bpmp\b",
    "Security+": r"\bsecurity\+\b",
    "CISSP": r"\bcissp\b",
    "CPA": r"\bcpa\b",
    "Scrum": r"\bscrum master\b|\bcsm\b",
}
BEHAVIORAL_THEME_PATTERNS: dict[str, str] = {
    "Leadership": r"\blead(?:er|ership|ing)?\b",
    "Conflict Resolution": r"\bconflict\b|disagree",
    "Communication": r"\bcommunicat",
    "Ownership": r"\bownership\b|accountable|responsib",
    "Ambiguity": r"\bambiguity\b|uncertain|unclear",
    "Collaboration": r"\bcollaborat|\bteam\b",
    "Prioritization": r"\bprioriti[sz]e|deadline|trade-?off",
    "Failure/Learning": r"\bfail(?:ed|ure)?\b|learned",
}


@dataclass(frozen=True)
class DataSet:
    applications: list[JobApplication]
    companies: list[Company]
    interviews: list[Interview]
    emails: list[EmailMessage]
    resumes: list[Resume]
    cover_letters: list[CoverLetter]
    resume_analyses: list[ResumeMatchAnalysis]
    interview_prep_packages: list[InterviewPrepPackage]


class CareerIntelligenceService:
    """
    Builds a read-only career intelligence dashboard from existing ApplyTrack data.

    Deterministic analytics are computed first and are always returned. AI is a
    final interpretation step over those computed facts only; it never owns the
    metric calculations and a provider failure does not break the dashboard.
    """

    def __init__(self, db: Session, *, ai_client: AIClient | None = None) -> None:
        self.db = db
        self.repo = CareerIntelligenceRepository(db)
        self._injected_client = ai_client

    def build_dashboard(
        self,
        *,
        date_from: str | date | None = None,
        date_to: str | date | None = None,
        compare_date_from: str | date | None = None,
        compare_date_to: str | date | None = None,
    ) -> CareerIntelligenceResponse:
        filters = IntelligenceFilters(
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            compare_date_from=_parse_date(compare_date_from),
            compare_date_to=_parse_date(compare_date_to),
        )
        all_data = self._load_data()
        current = self._filter_data(all_data, filters.date_from, filters.date_to)

        application_metrics = self._application_metrics(current)
        company_insights = self._company_insights(current)
        resume_insights = self._document_insights(current, current.resumes, "resume_id")
        cover_letter_insights = self._document_insights(
            current, current.cover_letters, "cover_letter_id"
        )
        skill_intelligence = self._skill_intelligence(
            current,
            previous=self._filter_data(
                all_data, filters.compare_date_from, filters.compare_date_to
            )
            if filters.compare_date_from or filters.compare_date_to
            else None,
        )
        interview_intelligence = self._interview_intelligence(current)

        comparison = None
        if filters.compare_date_from or filters.compare_date_to:
            previous = self._filter_data(
                all_data, filters.compare_date_from, filters.compare_date_to
            )
            comparison = self._comparison(application_metrics, self._application_metrics(previous))

        facts = {
            "filters": filters.model_dump(mode="json"),
            "application_metrics": application_metrics.model_dump(mode="json"),
            "company_insights": company_insights.model_dump(mode="json"),
            "resume_insights": resume_insights.model_dump(mode="json"),
            "cover_letter_insights": cover_letter_insights.model_dump(mode="json"),
            "skill_intelligence": skill_intelligence.model_dump(mode="json"),
            "interview_intelligence": interview_intelligence.model_dump(mode="json"),
            "comparison": comparison.model_dump(mode="json") if comparison else None,
        }

        return CareerIntelligenceResponse(
            generated_at=datetime.now(UTC),
            filters=filters,
            application_metrics=application_metrics,
            company_insights=company_insights,
            resume_insights=resume_insights,
            cover_letter_insights=cover_letter_insights,
            skill_intelligence=skill_intelligence,
            interview_intelligence=interview_intelligence,
            ai_recommendations=self._ai_recommendations(facts),
            comparison=comparison,
        )

    def _load_data(self) -> DataSet:
        return DataSet(
            applications=self.repo.list_applications(),
            companies=self.repo.list_companies(),
            interviews=self.repo.list_interviews(),
            emails=self.repo.list_emails(),
            resumes=self.repo.list_resumes(),
            cover_letters=self.repo.list_cover_letters(),
            resume_analyses=self.repo.list_resume_analyses(),
            interview_prep_packages=self.repo.list_interview_prep_packages(),
        )

    def _filter_data(
        self, data: DataSet, date_from: date | None, date_to: date | None
    ) -> DataSet:
        application_ids = {
            app.id
            for app in data.applications
            if _in_range(_application_activity_date(app), date_from, date_to)
        }
        return DataSet(
            applications=[app for app in data.applications if app.id in application_ids],
            companies=data.companies,
            interviews=[
                item
                for item in data.interviews
                if item.application_id in application_ids
                and _in_range(item.scheduled_at.date(), date_from, date_to)
            ],
            emails=[
                item
                for item in data.emails
                if item.application_id in application_ids
                and _in_range(item.sent_at.date(), date_from, date_to)
            ],
            resumes=data.resumes,
            cover_letters=data.cover_letters,
            resume_analyses=[
                item
                for item in data.resume_analyses
                if _in_range(item.created_at.date(), date_from, date_to)
            ],
            interview_prep_packages=[
                item
                for item in data.interview_prep_packages
                if _in_range(item.created_at.date(), date_from, date_to)
            ],
        )

    def _application_metrics(self, data: DataSet) -> ApplicationMetrics:
        total = len(data.applications)
        responses = sum(1 for app in data.applications if self._has_response(app, data))
        interviewed = sum(1 for app in data.applications if self._has_interview(app, data))
        offers = sum(1 for app in data.applications if app.status in OFFER_STATUSES)
        accepted = sum(
            1 for app in data.applications if app.status == ApplicationStatus.ACCEPTED.value
        )
        rejected = sum(
            1 for app in data.applications if app.status == ApplicationStatus.REJECTED.value
        )
        ghosted = sum(
            1 for app in data.applications if app.status == ApplicationStatus.GHOSTED.value
        )
        active = sum(1 for app in data.applications if app.status not in TERMINAL_STATUSES)

        response_days = [
            days
            for app in data.applications
            if (days := self._days_until_first_response(app, data)) is not None
        ]
        interview_count = len(data.interviews)

        return ApplicationMetrics(
            total_applications=total,
            active_applications=active,
            response_rate=_rate(responses, total, "Applications with a response signal"),
            interview_rate=_rate(interviewed, total, "Applications with interviews"),
            offer_rate=_rate(offers, total, "Applications that reached offer"),
            offer_acceptance_rate=_rate(accepted, offers, "Accepted offers / all offers"),
            rejection_rate=_rate(rejected, total, "Applications marked rejected"),
            ghost_rate=_rate(ghosted, total, "Applications marked ghosted"),
            average_days_until_first_response=_avg(response_days),
            average_interview_count_per_application=(
                _round(interview_count / total) if total else None
            ),
        )

    def _company_insights(self, data: DataSet) -> CompanyInsights:
        companies = {company.id: company for company in data.companies}
        company_segments: dict[str, list[JobApplication]] = defaultdict(list)
        industry_segments: dict[str, list[JobApplication]] = defaultdict(list)
        location_segments: dict[str, list[JobApplication]] = defaultdict(list)

        for app in data.applications:
            company = companies.get(app.company_id)
            if not company:
                continue
            company_segments[company.name].append(app)
            industry_segments[company.industry or "Unknown"].append(app)
            location_segments[app.location or company.location or "Unknown"].append(app)

        return CompanyInsights(
            most_responsive_companies=self._rank_segments(company_segments, data),
            most_responsive_industries=self._rank_segments(industry_segments, data),
            most_responsive_locations=self._rank_segments(location_segments, data),
            fastest_response_companies=self._rank_segments(
                company_segments, data, sort_by_fastest=True
            ),
        )

    def _document_insights(
        self,
        data: DataSet,
        documents: Iterable[Resume | CoverLetter],
        attr_name: str,
    ) -> DocumentInsights:
        by_id = {doc.id: doc for doc in documents}
        items: list[DocumentPerformance] = []

        for doc_id, doc in by_id.items():
            apps = [app for app in data.applications if getattr(app, attr_name) == doc_id]
            if not apps:
                continue
            total = len(apps)
            responses = sum(1 for app in apps if self._has_response(app, data))
            interviews = sum(1 for app in apps if self._has_interview(app, data))
            offers = sum(1 for app in apps if app.status in OFFER_STATUSES)
            items.append(
                DocumentPerformance(
                    id=doc.id,
                    name=doc.name,
                    version=doc.version,
                    submitted_applications=total,
                    response_rate=_rate_value(responses, total),
                    interview_rate=_rate_value(interviews, total),
                    offer_rate=_rate_value(offers, total),
                )
            )

        items.sort(
            key=lambda item: (
                item.submitted_applications,
                item.interview_rate or 0,
                item.response_rate or 0,
                item.offer_rate or 0,
            ),
            reverse=True,
        )
        return DocumentInsights(
            items=items,
            highest_interview_rate=_best_document(items, "interview_rate"),
            highest_response_rate=_best_document(items, "response_rate"),
            highest_offer_rate=_best_document(items, "offer_rate"),
        )

    def _skill_intelligence(
        self, data: DataSet, *, previous: DataSet | None = None
    ) -> SkillIntelligence:
        descriptions = self._job_descriptions(data)
        previous_descriptions = self._job_descriptions(previous) if previous else []
        requested = _scan_patterns(descriptions, SKILL_PATTERNS)
        previous_requested = _scan_patterns(previous_descriptions, SKILL_PATTERNS)
        missing = Counter()
        for analysis in data.resume_analyses:
            for skill in (analysis.result or {}).get("missing_skills", []):
                if isinstance(skill, str) and skill.strip():
                    missing[skill.strip()] += 1

        certs = _scan_patterns(descriptions, CERTIFICATION_PATTERNS)
        trends = []
        for skill in TECHNOLOGY_SKILLS:
            current_count = requested[skill]
            previous_count = previous_requested[skill]
            if current_count or previous_count:
                trends.append(
                    TrendInsight(
                        name=skill,
                        current_count=current_count,
                        previous_count=previous_count,
                        delta=current_count - previous_count,
                    )
                )
        trends.sort(key=lambda item: (item.delta, item.current_count), reverse=True)

        return SkillIntelligence(
            job_description_count=len(descriptions),
            most_requested_skills=_count_insights(requested, len(descriptions)),
            missing_skills=_count_insights(missing, len(data.resume_analyses)),
            trending_technologies=trends[:10],
            frequently_requested_certifications=_count_insights(certs, len(descriptions)),
        )

    def _interview_intelligence(self, data: DataSet) -> InterviewIntelligence:
        type_counts = Counter(
            interview.interview_type or "other" for interview in data.interviews
        )
        offered_apps = [app for app in data.applications if app.status in OFFER_STATUSES]
        counts_before_offer = [
            len([iv for iv in data.interviews if iv.application_id == app.id])
            for app in offered_apps
        ]

        technical_topics = Counter()
        behavioral_themes = Counter()
        for package in data.interview_prep_packages:
            result = package.result or {}
            study_topics = result.get("study_topics") or {}
            if isinstance(study_topics, dict):
                for values in study_topics.values():
                    technical_topics.update(_clean_strings(values))
            likely_questions = result.get("likely_questions") or {}
            if isinstance(likely_questions, dict):
                technical_topics.update(_keywords_from_strings(likely_questions.get("technical")))
                technical_topics.update(
                    _keywords_from_strings(likely_questions.get("role_specific"))
                )
                behavioral_themes.update(
                    _scan_text_patterns(
                        _clean_strings(likely_questions.get("behavioral")),
                        BEHAVIORAL_THEME_PATTERNS,
                    )
                )
            star_examples = result.get("star_examples") or []
            if isinstance(star_examples, list):
                behavioral_themes.update(
                    _scan_text_patterns(
                        [
                            str(item.get("question", ""))
                            for item in star_examples
                            if isinstance(item, dict)
                        ],
                        BEHAVIORAL_THEME_PATTERNS,
                    )
                )

        return InterviewIntelligence(
            most_common_interview_types=_count_insights(type_counts, len(data.interviews)),
            average_interviews_before_offer=_avg(counts_before_offer),
            common_technical_topics=_count_insights(technical_topics, None),
            common_behavioral_themes=_count_insights(behavioral_themes, None),
        )

    def _comparison(
        self, current: ApplicationMetrics, previous: ApplicationMetrics
    ) -> PeriodComparison:
        pairs = [
            ("Total applications", current.total_applications, previous.total_applications),
            ("Response rate", current.response_rate.value, previous.response_rate.value),
            ("Interview rate", current.interview_rate.value, previous.interview_rate.value),
            ("Offer rate", current.offer_rate.value, previous.offer_rate.value),
            ("Ghost rate", current.ghost_rate.value, previous.ghost_rate.value),
            (
                "Average days to response",
                current.average_days_until_first_response,
                previous.average_days_until_first_response,
            ),
        ]
        return PeriodComparison(
            metrics=[
                ComparisonMetric(
                    name=name,
                    current=_number_or_none(curr),
                    previous=_number_or_none(prev),
                    delta=(
                        _round(float(curr) - float(prev))
                        if curr is not None and prev is not None
                        else None
                    ),
                )
                for name, curr, prev in pairs
            ]
        )

    def _ai_recommendations(self, facts: dict) -> AIRecommendations:
        fallback = self._deterministic_recommendations(facts)
        if self._not_enough_data(facts):
            return AIRecommendations(
                available=False,
                executive_summary=fallback.executive_summary,
                recommendations=fallback.recommendations,
                caveats=fallback.caveats,
            )

        try:
            prompt = render_template(
                PROMPT_TEMPLATE,
                {"analytics_json": json.dumps(facts, sort_keys=True)},
            )
            client = self._resolve_client(fallback)
            structured = client.generate_structured(
                GenerationRequest(
                    system=prompt.system,
                    prompt=prompt.user,
                    temperature=0.2,
                ),
                AIRecommendationResult,
                db=self.db,
                feature=FEATURE,
            )
            return AIRecommendations(
                available=True,
                provider=structured.result.provider,
                model=structured.result.model,
                executive_summary=structured.data.executive_summary,
                recommendations=structured.data.recommendations,
                caveats=structured.data.caveats,
            )
        except AIError as exc:
            logger.warning("Career intelligence AI recommendations unavailable: %s", exc)
            return AIRecommendations(
                available=False,
                executive_summary=(
                    "Deterministic analytics are available, but AI recommendations "
                    "could not be generated."
                ),
                recommendations=fallback.recommendations,
                caveats=[*fallback.caveats, "AI provider unavailable or returned invalid output."],
            )

    def _resolve_client(self, fallback: AIRecommendationResult) -> AIClient:
        if self._injected_client is not None:
            return self._injected_client
        if settings.ai_active_provider == "mock":
            return AIClient(
                MockProvider(default_response=fallback.model_dump_json()),
                default_model=settings.AI_MODEL,
            )
        return get_ai_client()

    def _deterministic_recommendations(self, facts: dict) -> AIRecommendationResult:
        metrics = facts["application_metrics"]
        skills = facts["skill_intelligence"]
        companies = facts["company_insights"]
        recs: list[AIRecommendation] = []
        caveats: list[str] = []

        total = metrics["total_applications"]
        if total < 5:
            caveats.append(
                "The sample size is small; treat recommendations as directional."
            )
        if skills["job_description_count"] == 0:
            caveats.append(
                "No stored job descriptions were available for skill intelligence."
            )

        interview_rate = metrics["interview_rate"]["value"]
        response_rate = metrics["response_rate"]["value"]
        ghost_rate = metrics["ghost_rate"]["value"]
        top_skill = _first(skills["most_requested_skills"])
        top_company = _first(companies["most_responsive_companies"])
        fastest_company = _first(companies["fastest_response_companies"])
        best_resume = facts["resume_insights"]["highest_interview_rate"]
        best_cover_letter = facts["cover_letter_insights"]["highest_response_rate"]

        if top_skill:
            recs.append(
                AIRecommendation(
                    title=f"Emphasize {top_skill['name']}",
                    detail=(
                        f"{top_skill['name']} appears in {top_skill['count']} stored "
                        "job descriptions. Review resume and cover-letter language "
                        "for truthful, evidence-backed coverage."
                    ),
                    evidence=f"{top_skill['percentage']}% of stored job descriptions",
                )
            )
        if best_resume:
            recs.append(
                AIRecommendation(
                    title="Reuse the strongest resume version",
                    detail=(
                        f"{best_resume['name']} v{best_resume['version']} has the "
                        "highest interview rate among linked resume versions."
                    ),
                    evidence=(
                        f"{best_resume['interview_rate']}% interview rate across "
                        f"{best_resume['submitted_applications']} applications"
                    ),
                )
            )
        if best_cover_letter:
            recs.append(
                AIRecommendation(
                    title="Study the best-performing cover letter",
                    detail=(
                        f"{best_cover_letter['name']} v{best_cover_letter['version']} "
                        "has the strongest response rate among linked cover letters."
                    ),
                    evidence=(
                        f"{best_cover_letter['response_rate']}% response rate across "
                        f"{best_cover_letter['submitted_applications']} applications"
                    ),
                )
            )
        if top_company:
            recs.append(
                AIRecommendation(
                    title=f"Prioritize segments like {top_company['name']}",
                    detail=(
                        "This company or segment has produced the strongest response "
                        "signals in your tracked history."
                    ),
                    evidence=f"{top_company['response_rate']}% response rate",
                )
            )
        if fastest_company and fastest_company.get("average_days_until_first_response"):
            recs.append(
                AIRecommendation(
                    title="Follow up using fastest-response patterns",
                    detail=(
                        f"{fastest_company['name']} has the fastest observed response "
                        "cycle. Compare source, role, and outreach notes for repeatable patterns."
                    ),
                    evidence=(
                        f"{fastest_company['average_days_until_first_response']} days "
                        "average to first response"
                    ),
                )
            )
        if (
            response_rate is not None
            and interview_rate is not None
            and response_rate > interview_rate
        ):
            recs.append(
                AIRecommendation(
                    title="Improve response-to-interview conversion",
                    detail=(
                        "Your response rate is higher than your interview rate. Review "
                        "screening replies, recruiter notes, and resume match gaps."
                    ),
                    evidence=f"{response_rate}% response rate vs {interview_rate}% interview rate",
                )
            )
        if ghost_rate is not None and ghost_rate >= 30:
            recs.append(
                AIRecommendation(
                    title="Reduce ghosting risk with follow-up discipline",
                    detail=(
                        "A high ghost rate suggests follow-up timing and target quality "
                        "are worth reviewing."
                    ),
                    evidence=f"{ghost_rate}% ghost rate",
                )
            )

        if not recs:
            recs.append(
                AIRecommendation(
                    title="Add more tracked outcomes",
                    detail=(
                        "Create applications, link submitted documents, sync Gmail, "
                        "and record interviews so the dashboard can identify patterns."
                    ),
                    evidence=f"{total} tracked applications",
                )
            )

        summary = (
            "Career intelligence is based on computed CRM, Gmail, document, and AI "
            "history metrics. Recommendations cite only observed data."
        )
        return AIRecommendationResult(
            executive_summary=summary,
            recommendations=recs[:6],
            caveats=caveats,
        )

    @staticmethod
    def _not_enough_data(facts: dict) -> bool:
        return (
            facts["application_metrics"]["total_applications"] == 0
            and facts["skill_intelligence"]["job_description_count"] == 0
        )

    def _rank_segments(
        self,
        segments: dict[str, list[JobApplication]],
        data: DataSet,
        *,
        sort_by_fastest: bool = False,
    ) -> list[SegmentInsight]:
        rows: list[SegmentInsight] = []
        for name, apps in segments.items():
            total = len(apps)
            responses = sum(1 for app in apps if self._has_response(app, data))
            response_days = [
                days
                for app in apps
                if (days := self._days_until_first_response(app, data)) is not None
            ]
            rows.append(
                SegmentInsight(
                    name=name,
                    total_applications=total,
                    responses=responses,
                    response_rate=_rate_value(responses, total),
                    average_days_until_first_response=_avg(response_days),
                )
            )
        if sort_by_fastest:
            rows = [row for row in rows if row.average_days_until_first_response is not None]
            rows.sort(
                key=lambda row: (
                    row.average_days_until_first_response or 999999,
                    -row.total_applications,
                )
            )
        else:
            rows.sort(
                key=lambda row: (row.response_rate or 0, row.responses, row.total_applications),
                reverse=True,
            )
        return rows[:5]

    def _has_response(self, app: JobApplication, data: DataSet) -> bool:
        if app.status in RESPONSE_STATUSES:
            return True
        return any(
            email.application_id == app.id and email.direction == "inbound"
            for email in data.emails
        ) or self._has_interview(app, data)

    @staticmethod
    def _has_interview(app: JobApplication, data: DataSet) -> bool:
        return app.status in INTERVIEW_STATUSES or any(
            interview.application_id == app.id for interview in data.interviews
        )

    @staticmethod
    def _days_until_first_response(app: JobApplication, data: DataSet) -> float | None:
        start = app.date_applied
        if start is None:
            return None
        dates: list[date] = [
            email.sent_at.date()
            for email in data.emails
            if email.application_id == app.id
            and email.direction == "inbound"
            and email.sent_at.date() >= start
        ]
        dates.extend(
            interview.scheduled_at.date()
            for interview in data.interviews
            if interview.application_id == app.id and interview.scheduled_at.date() >= start
        )
        if not dates:
            return None
        return float((min(dates) - start).days)

    @staticmethod
    def _job_descriptions(data: DataSet | None) -> list[str]:
        if data is None:
            return []
        descriptions = [item.job_description for item in data.resume_analyses]
        descriptions.extend(item.job_description for item in data.interview_prep_packages)
        return [text for text in descriptions if text and text.strip()]


def _parse_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _application_activity_date(app: JobApplication) -> date:
    return app.date_applied or app.created_at.date()


def _in_range(value: date, date_from: date | None, date_to: date | None) -> bool:
    if date_from and value < date_from:
        return False
    if date_to and value > date_to:
        return False
    return True


def _rate(numerator: int, denominator: int, label: str) -> RateMetric:
    return RateMetric(
        value=_rate_value(numerator, denominator),
        numerator=numerator,
        denominator=denominator,
        label=label,
    )


def _rate_value(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return _round(numerator / denominator * 100)


def _round(value: float) -> float:
    return round(value, 2)


def _avg(values: Iterable[float | int]) -> float | None:
    data = list(values)
    if not data:
        return None
    return _round(float(mean(data)))


def _number_or_none(value: float | int | None) -> float | None:
    return float(value) if value is not None else None


def _best_document(
    items: list[DocumentPerformance], field_name: str
) -> DocumentPerformance | None:
    scored = [item for item in items if getattr(item, field_name) is not None]
    if not scored:
        return None
    return max(
        scored,
        key=lambda item: (
            getattr(item, field_name) or 0,
            item.submitted_applications,
        ),
    )


def _scan_patterns(texts: Iterable[str], patterns: dict[str, str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        for name, pattern in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                counts[name] += 1
    return counts


def _scan_text_patterns(texts: Iterable[str], patterns: dict[str, str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        for name, pattern in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                counts[name] += 1
    return counts


def _count_insights(
    counts: Counter[str], denominator: int | None, limit: int = 10
) -> list[CountInsight]:
    rows = []
    for name, count in counts.most_common(limit):
        rows.append(
            CountInsight(
                name=name,
                count=count,
                percentage=_rate_value(count, denominator) if denominator else None,
            )
        )
    return rows


def _clean_strings(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _keywords_from_strings(values: object) -> Counter[str]:
    text = " ".join(_clean_strings(values))
    return _scan_patterns([text], SKILL_PATTERNS) if text else Counter()


def _first(values: list[dict] | list | None) -> dict | None:
    if not values:
        return None
    value = values[0]
    return value if isinstance(value, dict) else None
