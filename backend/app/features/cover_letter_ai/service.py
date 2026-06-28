import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.core.config import settings
from app.exceptions.http import ValidationError
from app.features.applications.repository import ApplicationRepository
from app.features.companies.repository import CompanyRepository
from app.features.cover_letter_ai.schemas import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    CoverLetterGeneration,
    CoverLetterSaveRequest,
    CoverLetterVersionContent,
    UsageSummary,
)
from app.features.cover_letter_ai.simulation import simulated_cover_letter
from app.features.cover_letters.model import CoverLetter
from app.features.cover_letters.service import CoverLetterService
from app.features.resume_match.text_extraction import extract_text
from app.features.resumes.service import ResumeService

logger = logging.getLogger(__name__)

FEATURE = "cover_letter_ai"
PROMPT_TEMPLATE = "cover_letter.v1"
# Slightly higher than analytical features — cover letters benefit from a little
# creativity while staying grounded in the resume.
GENERATION_TEMPERATURE = 0.5


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "cover-letter"


class CoverLetterAIService:
    """
    Generates cover letters via the shared AI platform and persists them as
    versions in the existing Cover Letter Library.

    It owns no database table of its own — generation history is the library's
    version history. The service composes existing building blocks (resume +
    cover-letter libraries, applications, companies, the AI platform) and holds
    no provider-specific code or inline prompts.

    `ai_client` is injectable for tests; otherwise the client is resolved per
    request so mock-mode simulation can personalise output to the company/role.
    """

    def __init__(self, db: Session, user_id: UUID, *, ai_client: AIClient | None = None) -> None:
        self.db = db
        self.user_id = user_id
        self.resume_service = ResumeService(db, user_id)
        self.cover_letter_service = CoverLetterService(db, user_id)
        self.application_repo = ApplicationRepository(db)
        self.company_repo = CompanyRepository(db)
        self._injected_client = ai_client

    def _resolve_client(self, company_name: str, job_title: str) -> AIClient:
        if self._injected_client is not None:
            return self._injected_client
        if settings.ai_active_provider == "mock":
            # Offline simulation personalised to the resolved company/role; still
            # flows through generate_structured (parse + usage tracking).
            provider = MockProvider(
                handler=lambda _req: simulated_cover_letter(company_name, job_title)
            )
            return AIClient(provider, default_model=settings.AI_MODEL)
        return get_ai_client()

    def generate(
        self, data: CoverLetterGenerateRequest
    ) -> CoverLetterGenerateResponse:
        # Load + extract the resume (raises NotFoundError if missing).
        downloaded = self.resume_service.download(data.resume_id)
        resume = downloaded.record
        resume_text = extract_text(resume.file_name, downloaded.content)

        company_name, job_title = self._resolve_company_and_title(data)

        # Optional style template — reuse the resume extractor so any library
        # format (md/txt/docx/pdf) is supported.
        template_text = "None"
        if data.template_cover_letter_id is not None:
            tmpl = self.cover_letter_service.download(data.template_cover_letter_id)
            template_text = extract_text(tmpl.record.file_name, tmpl.content)

        prompt = render_template(
            PROMPT_TEMPLATE,
            {
                "company_name": company_name,
                "job_title": job_title,
                "job_description": data.job_description,
                "resume_text": resume_text,
                "template": template_text,
                "user_notes": (data.user_notes or "None"),
            },
        )

        client = self._resolve_client(company_name, job_title)
        structured = client.generate_structured(
            GenerationRequest(
                system=prompt.system,
                prompt=prompt.user,
                temperature=GENERATION_TEMPERATURE,
            ),
            CoverLetterGeneration,
            db=self.db,
            feature=FEATURE,
            user_id=self.user_id,
        )
        generation = structured.data
        result = structured.result

        logger.info(
            "Generated cover letter resume_id=%s company=%r title=%r provider=%s tokens=%d",
            data.resume_id,
            company_name,
            job_title,
            result.provider,
            result.usage.total_tokens,
        )

        return CoverLetterGenerateResponse(
            markdown=generation.markdown,
            plain_text=generation.plain_text,
            resume_name=f"{resume.name} (v{resume.version})",
            company_name=company_name,
            job_title=job_title,
            usage=UsageSummary(
                provider=result.provider,
                model=result.model,
                prompt_tokens=result.usage.prompt_tokens,
                completion_tokens=result.usage.completion_tokens,
                total_tokens=result.usage.total_tokens,
                estimated_cost_usd=result.estimated_cost_usd,
                latency_ms=result.latency_ms,
            ),
        )

    def _resolve_company_and_title(
        self, data: CoverLetterGenerateRequest
    ) -> tuple[str, str]:
        """Resolve company + title from explicit input, falling back to the
        selected application. Explicit values always win."""
        company_name = (data.company_name or "").strip()
        job_title = (data.job_title or "").strip()

        if data.application_id is not None:
            application = self.application_repo.get_or_raise_for_user(
                data.application_id,
                self.user_id,
            )
            company = self.company_repo.get_or_raise_for_user(
                application.company_id,
                self.user_id,
            )
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

    def save_version(self, data: CoverLetterSaveRequest) -> CoverLetter:
        """Save the (possibly edited) letter as a new version in the library.

        Reuses CoverLetterService.upload, which auto-assigns the next version for
        documents sharing the same name — so repeated saves under one name build
        a version history with no extra code here.
        """
        record = self.cover_letter_service.upload(
            file_name=f"{_slugify(data.name)}.md",
            content=data.content.encode("utf-8"),
            name=data.name,
            notes=data.notes,
        )
        logger.info(
            "Saved cover letter version id=%s name=%r v%d",
            record.id,
            record.name,
            record.version,
        )
        return record

    def list_versions(self, name: str) -> list[CoverLetterVersionContent]:
        """All versions (with text) of a named cover letter, newest first.

        Powers the UI's "compare with previous versions" without N download
        round-trips.
        """
        records, _ = self.cover_letter_service.list(name=name, limit=100)
        versions: list[CoverLetterVersionContent] = []
        for record in records:
            content = self.cover_letter_service.download(record.id).content.decode(
                "utf-8", errors="replace"
            )
            versions.append(
                CoverLetterVersionContent(
                    id=record.id,
                    name=record.name,
                    version=record.version,
                    file_name=record.file_name,
                    created_at=record.created_at,
                    content=content,
                )
            )
        return versions
