import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.core.config import settings
from app.exceptions.http import ValidationError
from app.features.applications.model import JobApplication
from app.features.applications.repository import ApplicationRepository
from app.features.companies.repository import CompanyRepository
from app.features.gmail.repository import EmailMessageRepository
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.interview_ai.repository import InterviewPrepRepository
from app.features.interview_ai.schemas import InterviewPrepRequest, InterviewPrepResult
from app.features.interview_ai.simulation import simulated_interview_prep
from app.features.interviews.repository import InterviewRepository
from app.features.recruiters.repository import RecruiterRepository
from app.features.resume_match.text_extraction import extract_text
from app.features.resumes.service import ResumeService

logger = logging.getLogger(__name__)

FEATURE = "interview_prep"
PROMPT_TEMPLATE = "interview_prep.v1"
GENERATION_TEMPERATURE = 0.4
MAX_CONTEXT_EMAILS = 5
# Bound the gathered context so token usage stays predictable.
MAX_CONTEXT_CHARS = 6_000


class InterviewPrepService:
    """
    Generates and stores interview-preparation packages via the shared AI
    platform, reusing existing data: applications, companies, the resume
    library, interviews, recruiters, and imported Gmail.

    Holds no provider-specific code and no inline prompts. The AI client is
    injectable for tests; otherwise resolved per request so mock-mode simulation
    can personalise output.
    """

    def __init__(self, db: Session, *, ai_client: AIClient | None = None) -> None:
        self.db = db
        self.repo = InterviewPrepRepository(db)
        self.resume_service = ResumeService(db)
        self.application_repo = ApplicationRepository(db)
        self.company_repo = CompanyRepository(db)
        self.interview_repo = InterviewRepository(db)
        self.recruiter_repo = RecruiterRepository(db)
        self.email_repo = EmailMessageRepository(db)
        self._injected_client = ai_client

    # -- client resolution --------------------------------------------------

    def _resolve_client(
        self, company_name: str, job_title: str, interview_type: str
    ) -> AIClient:
        if self._injected_client is not None:
            return self._injected_client
        if settings.ai_active_provider == "mock":
            provider = MockProvider(
                handler=lambda _req: simulated_interview_prep(
                    company_name, job_title, interview_type
                )
            )
            return AIClient(provider, default_model=settings.AI_MODEL)
        return get_ai_client()

    # -- main flow ----------------------------------------------------------

    def create(self, data: InterviewPrepRequest) -> InterviewPrepPackage:
        application: JobApplication | None = None
        if data.application_id is not None:
            application = self.application_repo.get_or_raise(data.application_id)

        company_name, job_title = self._resolve_company_title(data, application)
        resume_id, resume_text = self._resolve_resume(data, application)
        interview_type = (data.interview_type or "General").strip()
        interview_round = (data.interview_round or "").strip() or None
        additional_context = self._gather_context(data, application)

        prompt = render_template(
            PROMPT_TEMPLATE,
            {
                "company_name": company_name,
                "job_title": job_title,
                "interview_type": interview_type,
                "interview_round": interview_round or "Not specified",
                "job_description": data.job_description,
                "resume_text": resume_text,
                "additional_context": additional_context,
            },
        )

        client = self._resolve_client(company_name, job_title, interview_type)
        structured = client.generate_structured(
            GenerationRequest(
                system=prompt.system,
                prompt=prompt.user,
                temperature=GENERATION_TEMPERATURE,
            ),
            InterviewPrepResult,
            db=self.db,
            feature=FEATURE,
        )
        result = structured.data
        ai = structured.result

        package = self.repo.create(
            {
                "application_id": data.application_id,
                "resume_id": resume_id,
                "company_name": company_name,
                "job_title": job_title,
                "interview_type": interview_type,
                "interview_round": interview_round,
                "job_description": data.job_description,
                "result": result.model_dump(),
                "provider": ai.provider,
                "model": ai.model,
                "prompt_tokens": ai.usage.prompt_tokens,
                "completion_tokens": ai.usage.completion_tokens,
                "total_tokens": ai.usage.total_tokens,
                "estimated_cost_usd": (
                    Decimal(str(ai.estimated_cost_usd))
                    if ai.estimated_cost_usd is not None
                    else None
                ),
                "latency_ms": ai.latency_ms,
            }
        )
        logger.info(
            "Generated interview prep id=%s company=%r title=%r type=%r provider=%s tokens=%d",
            package.id,
            company_name,
            job_title,
            interview_type,
            ai.provider,
            ai.usage.total_tokens,
        )
        return package

    def get(self, package_id: UUID) -> InterviewPrepPackage:
        return self.repo.get_or_raise(package_id)

    def list(
        self,
        *,
        application_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[InterviewPrepPackage], int]:
        return self.repo.list_paginated(
            application_id=application_id, skip=skip, limit=limit
        )

    def delete(self, package_id: UUID) -> None:
        package = self.repo.get_or_raise(package_id)
        self.repo.delete(package)
        logger.info("Deleted interview prep id=%s", package_id)

    # -- helpers ------------------------------------------------------------

    def _resolve_company_title(
        self, data: InterviewPrepRequest, application: JobApplication | None
    ) -> tuple[str, str]:
        company_name = (data.company_name or "").strip()
        job_title = (data.job_title or "").strip()
        if application is not None:
            company = self.company_repo.get_or_raise(application.company_id)
            company_name = company_name or company.name
            job_title = job_title or application.job_title
        if not company_name:
            raise ValidationError(
                "A company name is required — provide one or select an application."
            )
        if not job_title:
            raise ValidationError(
                "A job title is required — provide one or select an application."
            )
        return company_name, job_title

    def _resolve_resume(
        self, data: InterviewPrepRequest, application: JobApplication | None
    ) -> tuple[UUID | None, str]:
        # Explicit resume wins; otherwise fall back to the application's
        # submitted resume (set in the Applications feature).
        resume_id = data.resume_id or (
            application.resume_id if application is not None else None
        )
        if resume_id is None:
            return None, "Not provided."
        downloaded = self.resume_service.download(resume_id)
        text = extract_text(downloaded.record.file_name, downloaded.content)
        return resume_id, text

    def _gather_context(
        self, data: InterviewPrepRequest, application: JobApplication | None
    ) -> str:
        """Assemble grounding context from provided fields + stored data.

        Reuses interviews, recruiters, and imported Gmail. Only non-empty
        sections are included; the whole block is capped to bound tokens.
        """
        parts: list[str] = []

        if data.recruiter_notes:
            parts.append(f"Recruiter notes (provided):\n{data.recruiter_notes.strip()}")
        if data.interview_notes:
            parts.append(
                f"Interview notes (provided):\n{data.interview_notes.strip()}"
            )

        if application is not None:
            if application.notes:
                parts.append(f"Application notes:\n{application.notes.strip()}")

            interviews, _ = self.interview_repo.list_paginated(
                application_id=application.id, limit=20
            )
            interview_lines = []
            for iv in interviews:
                bits = [iv.interview_type or "interview"]
                if iv.notes:
                    bits.append(f"notes: {iv.notes.strip()}")
                if iv.feedback:
                    bits.append(f"feedback: {iv.feedback.strip()}")
                if len(bits) > 1:
                    interview_lines.append(" — ".join(bits))
            if interview_lines:
                parts.append(
                    "Stored interview records:\n"
                    + "\n".join(f"- {line}" for line in interview_lines)
                )

            recruiters, _ = self.recruiter_repo.list_paginated(
                company_id=application.company_id, limit=10
            )
            recruiter_notes = [r.notes.strip() for r in recruiters if r.notes]
            if recruiter_notes:
                parts.append(
                    "Recruiter notes (stored):\n"
                    + "\n".join(f"- {note}" for note in recruiter_notes)
                )

            emails, _ = self.email_repo.list_filtered(
                application_id=application.id, limit=MAX_CONTEXT_EMAILS
            )
            if emails:
                email_lines = []
                for e in emails:
                    who = e.sender_name or e.sender
                    preview = (e.body_preview or "").strip()[:200]
                    subject = e.subject or "(no subject)"
                    email_lines.append(f"- [{e.direction}] {who}: {subject} — {preview}")
                parts.append("Recent related emails:\n" + "\n".join(email_lines))

        text = "\n\n".join(parts).strip()
        if len(text) > MAX_CONTEXT_CHARS:
            text = text[:MAX_CONTEXT_CHARS].rstrip() + "\n…[truncated]"
        return text or "None"
