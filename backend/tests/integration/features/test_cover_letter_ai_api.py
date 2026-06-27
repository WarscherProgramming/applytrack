import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.mock_provider import MockProvider
from app.ai.usage_tracker import AIUsageRecord
from app.exceptions.http import ValidationError
from app.features.applications.repository import ApplicationRepository
from app.features.companies.repository import CompanyRepository
from app.features.cover_letter_ai.router import _get_service
from app.features.cover_letter_ai.schemas import (
    CoverLetterGenerateRequest,
    CoverLetterSaveRequest,
)
from app.features.cover_letter_ai.service import CoverLetterAIService
from app.features.cover_letters.service import CoverLetterService
from app.features.resumes.service import ResumeService
from app.main import app

_GEN_JSON = json.dumps(
    {
        "markdown": "# Cover Letter\n\nDear Acme Hiring Team,\n\nI am a great fit.",
        "plain_text": "Dear Acme Hiring Team,\n\nI am a great fit.",
    }
)

_JOB_DESCRIPTION = (
    "Senior backend engineer with Python and FastAPI experience required. "
    "PostgreSQL and Docker are a plus."
)


def _mock_client(response: str = _GEN_JSON) -> AIClient:
    return AIClient(
        MockProvider(default_response=response), default_model="mock-model"
    )


def _create_resume(db: Session, *, content: bytes = b"Python engineer, 6 years.") -> str:
    resume = ResumeService(db).upload(
        file_name="resume.txt", content=content, name="My Resume"
    )
    return str(resume.id)


def _create_application(db: Session) -> tuple[str, str]:
    company = CompanyRepository(db).create({"name": "Acme"})
    application = ApplicationRepository(db).create(
        {"company_id": company.id, "job_title": "Senior Engineer"}
    )
    return str(application.id), company.name


def _inject(db: Session, ai_client: AIClient) -> None:
    app.dependency_overrides[_get_service] = lambda: CoverLetterAIService(
        db, ai_client=ai_client
    )


class TestServiceGenerate:
    def test_generates_with_explicit_company_and_title(self, db: Session) -> None:
        resume_id = _create_resume(db)
        service = CoverLetterAIService(db, ai_client=_mock_client())

        result = service.generate(
            CoverLetterGenerateRequest(
                resume_id=resume_id,
                job_description=_JOB_DESCRIPTION,
                company_name="Acme",
                job_title="Senior Engineer",
            )
        )

        assert result.markdown.startswith("# Cover Letter")
        assert result.plain_text
        assert result.company_name == "Acme"
        assert result.job_title == "Senior Engineer"
        assert result.resume_name == "My Resume (v1)"
        assert result.usage.total_tokens > 0

    def test_derives_company_and_title_from_application(self, db: Session) -> None:
        resume_id = _create_resume(db)
        application_id, company_name = _create_application(db)
        service = CoverLetterAIService(db, ai_client=_mock_client())

        result = service.generate(
            CoverLetterGenerateRequest(
                resume_id=resume_id,
                job_description=_JOB_DESCRIPTION,
                application_id=application_id,
            )
        )
        assert result.company_name == company_name
        assert result.job_title == "Senior Engineer"

    def test_tracks_ai_usage(self, db: Session) -> None:
        resume_id = _create_resume(db)
        CoverLetterAIService(db, ai_client=_mock_client()).generate(
            CoverLetterGenerateRequest(
                resume_id=resume_id,
                job_description=_JOB_DESCRIPTION,
                company_name="Acme",
                job_title="Engineer",
            )
        )
        usage = list(db.scalars(select(AIUsageRecord)))
        assert len(usage) == 1
        assert usage[0].feature == "cover_letter_ai"
        assert usage[0].success is True

    def test_uses_template_cover_letter(self, db: Session) -> None:
        resume_id = _create_resume(db)
        CoverLetterService(db).upload(
            file_name="tmpl.md", content=b"Dear team, ...", name="My Template"
        )
        templates, _ = CoverLetterService(db).list(name="My Template")
        service = CoverLetterAIService(db, ai_client=_mock_client())

        result = service.generate(
            CoverLetterGenerateRequest(
                resume_id=resume_id,
                job_description=_JOB_DESCRIPTION,
                company_name="Acme",
                job_title="Engineer",
                template_cover_letter_id=templates[0].id,
            )
        )
        assert result.markdown

    def test_missing_company_and_title_raises(self, db: Session) -> None:
        resume_id = _create_resume(db)
        service = CoverLetterAIService(db, ai_client=_mock_client())
        with pytest.raises(ValidationError):
            service.generate(
                CoverLetterGenerateRequest(
                    resume_id=resume_id, job_description=_JOB_DESCRIPTION
                )
            )


class TestGenerateApi:
    def test_returns_generated_letter(self, client: TestClient, db: Session) -> None:
        resume_id = _create_resume(db)
        _inject(db, _mock_client())
        response = client.post(
            "/api/v1/cover-letter-ai/generate",
            json={
                "resume_id": resume_id,
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Acme",
                "job_title": "Senior Engineer",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["markdown"]
        assert body["plain_text"]
        assert body["usage"]["total_tokens"] > 0
        assert body["usage"]["provider"] == "mock"

    def test_simulation_works_without_injection(
        self, client: TestClient, db: Session
    ) -> None:
        # No injected client → offline simulation (no API key in tests).
        resume_id = _create_resume(db)
        response = client.post(
            "/api/v1/cover-letter-ai/generate",
            json={
                "resume_id": resume_id,
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Globex",
                "job_title": "Backend Engineer",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "Globex" in body["markdown"]
        assert body["plain_text"]

    def test_404_for_unknown_resume(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/cover-letter-ai/generate",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Acme",
                "job_title": "Engineer",
            },
        )
        assert response.status_code == 404

    def test_422_for_short_job_description(
        self, client: TestClient, db: Session
    ) -> None:
        resume_id = _create_resume(db)
        response = client.post(
            "/api/v1/cover-letter-ai/generate",
            json={
                "resume_id": resume_id,
                "job_description": "short",
                "company_name": "Acme",
                "job_title": "Engineer",
            },
        )
        assert response.status_code == 422

    def test_invalid_ai_json_returns_502(
        self, client: TestClient, db: Session
    ) -> None:
        resume_id = _create_resume(db)
        _inject(db, _mock_client(response="not json"))
        response = client.post(
            "/api/v1/cover-letter-ai/generate",
            json={
                "resume_id": resume_id,
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Acme",
                "job_title": "Engineer",
            },
        )
        assert response.status_code == 502


class TestSaveAndVersions:
    def test_save_creates_versions(self, client: TestClient, db: Session) -> None:
        first = client.post(
            "/api/v1/cover-letter-ai/save",
            json={"name": "Acme - Senior", "content": "Dear Acme, v1."},
        )
        assert first.status_code == 201
        assert first.json()["version"] == 1

        second = client.post(
            "/api/v1/cover-letter-ai/save",
            json={"name": "Acme - Senior", "content": "Dear Acme, v2."},
        )
        assert second.json()["version"] == 2

    def test_versions_endpoint_returns_content_newest_first(
        self, client: TestClient, db: Session
    ) -> None:
        client.post(
            "/api/v1/cover-letter-ai/save",
            json={"name": "Acme - Senior", "content": "Dear Acme, v1."},
        )
        client.post(
            "/api/v1/cover-letter-ai/save",
            json={"name": "Acme - Senior", "content": "Dear Acme, v2."},
        )

        versions = client.get(
            "/api/v1/cover-letter-ai/versions", params={"name": "Acme - Senior"}
        ).json()["items"]

        assert [v["version"] for v in versions] == [2, 1]
        assert versions[0]["content"] == "Dear Acme, v2."
        assert versions[1]["content"] == "Dear Acme, v1."

    def test_saved_letter_appears_in_cover_letter_library(
        self, client: TestClient, db: Session
    ) -> None:
        client.post(
            "/api/v1/cover-letter-ai/save",
            json={"name": "Library Check", "content": "Hello."},
        )
        # Reuses the existing Cover Letter Library list endpoint.
        listing = client.get(
            "/api/v1/cover-letters/", params={"name": "Library Check"}
        ).json()
        assert listing["total"] == 1
        assert listing["items"][0]["name"] == "Library Check"
