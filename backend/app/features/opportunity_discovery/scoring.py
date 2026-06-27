from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.companies.model import Company
from app.features.cover_letters.model import CoverLetter
from app.features.opportunity_discovery.schemas import NormalizedJobPosting, OpportunityScore
from app.features.resumes.model import Resume

RESPONSE_STATUSES = {
    ApplicationStatus.ASSESSMENT.value,
    ApplicationStatus.PHONE_SCREEN.value,
    ApplicationStatus.INTERVIEW.value,
    ApplicationStatus.FINAL_INTERVIEW.value,
    ApplicationStatus.OFFER.value,
    ApplicationStatus.ACCEPTED.value,
}


@dataclass(frozen=True)
class ResumeSkillProfile:
    id: UUID
    name: str
    version: int
    skills: set[str]

    @property
    def label(self) -> str:
        return f"{self.name} (v{self.version})"


@dataclass(frozen=True)
class ScoringContext:
    resume_profiles: list[ResumeSkillProfile]
    selected_resume_id: UUID | None
    cover_letters: list[CoverLetter]
    applications: list[JobApplication]
    companies: list[Company]
    preferred_location: str | None = None
    preferred_job_type: str | None = None
    preferred_industry: str | None = None


class OpportunityScoringEngine:
    """Deterministic opportunity scoring.

    Scores are grounded in stored resumes, stored applications/companies, and
    normalized provider data. AI explanation happens after this step.
    """

    def score(self, posting: NormalizedJobPosting, context: ScoringContext) -> OpportunityScore:
        job_skills = {skill.name for skill in posting.skills}
        resume = self._recommend_resume(job_skills, context)
        resume_skills = resume.skills if resume else set()
        matched_skills = sorted(job_skills & resume_skills)
        missing_skills = sorted(job_skills - resume_skills)

        skill_overlap = _percent(len(matched_skills), len(job_skills)) if job_skills else None
        resume_match = skill_overlap
        historical_rate = self._historical_response_rate(posting, context)
        location_score = self._location_score(posting, context.preferred_location)
        job_type_score = self._job_type_score(posting, context.preferred_job_type)
        industry_score = self._industry_score(posting, context.preferred_industry)

        components = [
            (resume_match, 40),
            (skill_overlap, 30),
            (location_score, 10),
            (job_type_score, 10),
            (_rate_to_score(historical_rate), 5),
            (industry_score, 5),
        ]
        available = [(score, weight) for score, weight in components if score is not None]
        overall = round(
            sum(score * weight for score, weight in available)
            / sum(weight for _, weight in available)
        ) if available else 0

        cover_letter = self._recommend_cover_letter(posting, context.cover_letters)
        reasoning = self._reasoning(
            posting=posting,
            resume=resume,
            skill_overlap=skill_overlap,
            historical_rate=historical_rate,
            location_score=location_score,
            job_type_score=job_type_score,
            industry_score=industry_score,
            missing_skills=missing_skills,
        )

        return OpportunityScore(
            overall_match_percent=max(0, min(100, overall)),
            resume_match_score=resume_match,
            skill_overlap_percent=skill_overlap,
            historical_response_rate=historical_rate,
            location_score=location_score,
            job_type_score=job_type_score,
            industry_score=industry_score,
            reasoning=reasoning,
            top_missing_skills=missing_skills[:5],
            matched_skills=matched_skills,
            recommended_resume_id=resume.id if resume else None,
            recommended_resume_name=resume.label if resume else None,
            suggested_cover_letter_id=cover_letter.id if cover_letter else None,
            suggested_cover_letter_name=_document_label(cover_letter) if cover_letter else None,
        )

    @staticmethod
    def _recommend_resume(
        job_skills: set[str], context: ScoringContext
    ) -> ResumeSkillProfile | None:
        if not context.resume_profiles:
            return None
        if context.selected_resume_id is not None:
            selected = [
                resume
                for resume in context.resume_profiles
                if resume.id == context.selected_resume_id
            ]
            if selected:
                return selected[0]
        return max(
            context.resume_profiles,
            key=lambda resume: (len(job_skills & resume.skills), resume.version, resume.name),
        )

    @staticmethod
    def _recommend_cover_letter(
        posting: NormalizedJobPosting, cover_letters: list[CoverLetter]
    ) -> CoverLetter | None:
        if not cover_letters:
            return None
        needles = {
            posting.company.lower(),
            *[part.lower() for part in posting.title.split() if len(part) >= 4],
        }

        def score(doc: CoverLetter) -> tuple[int, int, str]:
            haystack = f"{doc.name} {doc.notes or ''}".lower()
            matches = sum(1 for needle in needles if needle and needle in haystack)
            return matches, doc.version, doc.name

        return max(cover_letters, key=score)

    def _historical_response_rate(
        self, posting: NormalizedJobPosting, context: ScoringContext
    ) -> float | None:
        companies_by_id = {company.id: company for company in context.companies}
        exact_company = [
            application
            for application in context.applications
            if (
                company := companies_by_id.get(application.company_id)
            ) is not None
            and company.name.lower() == posting.company.lower()
        ]
        if exact_company:
            return _response_rate(exact_company)

        industry = posting.industry or context.preferred_industry
        if not industry:
            return None
        industry_apps = [
            application
            for application in context.applications
            if (
                company := companies_by_id.get(application.company_id)
            ) is not None
            and (company.industry or "").lower() == industry.lower()
        ]
        return _response_rate(industry_apps) if industry_apps else None

    @staticmethod
    def _location_score(
        posting: NormalizedJobPosting, preferred_location: str | None
    ) -> int | None:
        if not preferred_location:
            return None
        if posting.work_mode.value == "remote":
            return 100
        if posting.location and preferred_location.lower() in posting.location.lower():
            return 100
        if posting.location:
            return 35
        return None

    @staticmethod
    def _job_type_score(
        posting: NormalizedJobPosting, preferred_job_type: str | None
    ) -> int | None:
        if not preferred_job_type:
            return None
        haystack = f"{posting.employment_type or ''} {posting.title} {posting.description}".lower()
        return 100 if preferred_job_type.lower() in haystack else 40

    @staticmethod
    def _industry_score(
        posting: NormalizedJobPosting, preferred_industry: str | None
    ) -> int | None:
        if not preferred_industry:
            return None
        if posting.industry and preferred_industry.lower() in posting.industry.lower():
            return 100
        return 40

    @staticmethod
    def _reasoning(
        *,
        posting: NormalizedJobPosting,
        resume: ResumeSkillProfile | None,
        skill_overlap: int | None,
        historical_rate: float | None,
        location_score: int | None,
        job_type_score: int | None,
        industry_score: int | None,
        missing_skills: list[str],
    ) -> list[str]:
        rows: list[str] = []
        if skill_overlap is None:
            rows.append("No recognized skills were extracted from the posting.")
        elif resume:
            rows.append(f"{resume.label} overlaps with {skill_overlap}% of recognized skills.")
        else:
            rows.append("Upload a resume to compute resume skill overlap.")
        if missing_skills:
            rows.append(f"Top gaps: {', '.join(missing_skills[:5])}.")
        if historical_rate is not None:
            rows.append(
                "Historical response rate for comparable opportunities is "
                f"{historical_rate:.1f}%."
            )
        if location_score is not None:
            rows.append(f"Location preference score is {location_score}%.")
        if job_type_score is not None:
            rows.append(f"Job type preference score is {job_type_score}%.")
        if industry_score is not None:
            rows.append(f"Industry preference score is {industry_score}%.")
        rows.append(f"Source: {posting.provider.value} public job data.")
        return rows


def build_resume_profiles(resumes: list[Resume], skills_by_resume: dict[UUID, set[str]]):
    return [
        ResumeSkillProfile(
            id=resume.id,
            name=resume.name,
            version=resume.version,
            skills=skills_by_resume.get(resume.id, set()),
        )
        for resume in resumes
    ]


def _response_rate(applications: list[JobApplication]) -> float:
    if not applications:
        return 0.0
    responses = sum(1 for application in applications if application.status in RESPONSE_STATUSES)
    return round((responses / len(applications)) * 100, 1)


def _percent(value: int, total: int) -> int:
    if total <= 0:
        return 0
    return round((value / total) * 100)


def _rate_to_score(rate: float | None) -> int | None:
    return round(rate) if rate is not None else None


def _document_label(document: CoverLetter) -> str:
    return f"{document.name} (v{document.version})"
