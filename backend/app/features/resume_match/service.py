import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import GenerationRequest, MockProvider, get_ai_client, render_template
from app.ai.client import AIClient
from app.core.config import settings
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resume_match.repository import ResumeMatchRepository
from app.features.resume_match.schema import ResumeMatchCreate, ResumeMatchResult
from app.features.resume_match.simulation import simulated_match_response
from app.features.resume_match.text_extraction import extract_text
from app.features.resumes.service import ResumeService

logger = logging.getLogger(__name__)

# The feature label recorded against every AI usage row this service produces.
FEATURE = "resume_match"
PROMPT_TEMPLATE = "resume_match.v1"


class ResumeMatchService:
    """
    Orchestrates a Resume Match run on top of the shared AI platform.

    The flow is: load the resume file → extract text → render the central prompt
    → call the AI platform for structured output → persist history. The service
    holds no provider-specific code and no inline prompts; it depends only on
    app.ai's public surface, so swapping providers never touches this file.

    `ai_client` is injectable so tests pass an AIClient backed by MockProvider —
    no external calls, fully deterministic.
    """

    def __init__(self, db: Session, user_id: UUID, *, ai_client: AIClient | None = None) -> None:
        self.db = db
        self.user_id = user_id
        self.repo = ResumeMatchRepository(db)
        self.resume_service = ResumeService(db, user_id)
        self.ai_client = ai_client or self._default_client()

    @staticmethod
    def _default_client() -> AIClient:
        """The AI client to use when one isn't injected.

        In mock mode (no API key) we seed the MockProvider with a feature-shaped
        simulated response so the full pipeline works offline — the request still
        goes through generate_structured (parsing + usage tracking), so nothing
        bypasses the provider abstraction. With a real key, the shared client is
        used unchanged.
        """
        if settings.ai_active_provider == "mock":
            provider = MockProvider(
                handler=lambda request: simulated_match_response(request.prompt)
            )
            return AIClient(provider, default_model=settings.AI_MODEL)
        return get_ai_client()

    def create(self, data: ResumeMatchCreate) -> ResumeMatchAnalysis:
        # Load the resume bytes (raises NotFoundError if the resume is gone).
        downloaded = self.resume_service.download(data.resume_id)
        resume = downloaded.record
        resume_text = extract_text(resume.file_name, downloaded.content)
        resume_name = f"{resume.name} (v{resume.version})"

        prompt = render_template(
            PROMPT_TEMPLATE,
            {"resume_text": resume_text, "job_description": data.job_description},
        )

        structured = self.ai_client.generate_structured(
            GenerationRequest(system=prompt.system, prompt=prompt.user),
            ResumeMatchResult,
            db=self.db,
            feature=FEATURE,
            user_id=self.user_id,
        )
        result: ResumeMatchResult = structured.data

        analysis = self.repo.create(
            {
                "resume_id": data.resume_id,
                "resume_name": resume_name,
                "job_description": data.job_description,
                "overall_match_score": result.overall_match_score,
                "result": result.model_dump(),
                "provider": structured.result.provider,
                "model": structured.result.model,
                "user_id": self.user_id,
            }
        )
        logger.info(
            "Resume match analysis id=%s resume_id=%s score=%d provider=%s model=%s",
            analysis.id,
            data.resume_id,
            result.overall_match_score,
            structured.result.provider,
            structured.result.model,
        )
        return analysis

    def get(self, analysis_id: UUID) -> ResumeMatchAnalysis:
        return self.repo.get_or_raise_for_user(analysis_id, self.user_id)

    def list(
        self,
        *,
        resume_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ResumeMatchAnalysis], int]:
        return self.repo.list_paginated(
            resume_id=resume_id,
            user_id=self.user_id,
            skip=skip,
            limit=limit,
        )

    def delete(self, analysis_id: UUID) -> None:
        analysis = self.repo.get_or_raise_for_user(analysis_id, self.user_id)
        self.repo.delete(analysis)
        logger.info("Deleted resume match analysis id=%s", analysis_id)
