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
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.interview_ai.router import _get_service
from app.features.interview_ai.schemas import InterviewPrepRequest
from app.features.interview_ai.service import InterviewPrepService
from app.features.resumes.service import ResumeService
from app.features.users.model import User
from app.main import app

_RESULT = {
    "company_overview": {
        "mission": "Build great tools",
        "products_services": ["Platform", "API"],
        "industry": "Software",
        "culture": "Collaborative",
        "recent_news": "Based only on provided/stored data — no external lookup.",
    },
    "likely_questions": {
        "behavioral": ["Tell me about a conflict."],
        "technical": ["Explain REST vs RPC."],
        "role_specific": ["How do you design an API?"],
        "company_specific": ["Why us?"],
    },
    "star_examples": [
        {
            "question": "Biggest challenge?",
            "situation": "S",
            "task": "T",
            "action": "A",
            "result": "R",
        }
    ],
    "study_topics": {
        "languages": ["Python"],
        "frameworks": ["FastAPI"],
        "concepts": ["Concurrency"],
        "system_design": ["Rate limiting"],
        "algorithms": ["Hash maps"],
        "role_specific": ["API versioning"],
    },
    "questions_to_ask": ["What does success look like in 90 days?"],
    "red_flags": {
        "missing_resume_coverage": ["Kubernetes"],
        "skill_gaps": ["Terraform"],
        "likely_challenges": ["System design depth"],
    },
    "checklist": ["Research the company", "Prepare questions"],
}
_RESULT_JSON = json.dumps(_RESULT)

_JOB_DESCRIPTION = (
    "Senior backend engineer with Python and FastAPI experience required. "
    "PostgreSQL and Docker are a plus."
)


def _mock_client(response: str = _RESULT_JSON) -> AIClient:
    return AIClient(
        MockProvider(default_response=response), default_model="mock-model"
    )


def _create_resume(db: Session, user: User) -> str:
    resume = ResumeService(db, user.id).upload(
        file_name="resume.txt", content=b"Python engineer, 6 years.", name="R"
    )
    return str(resume.id)


def _create_application(
    db: Session, user: User, *, resume_id: str | None = None
) -> tuple[str, str]:
    company = CompanyRepository(db).create({"name": "Acme", "user_id": user.id})
    data = {
        "company_id": company.id,
        "job_title": "Senior Engineer",
        "user_id": user.id,
    }
    if resume_id is not None:
        data["resume_id"] = resume_id
    application = ApplicationRepository(db).create(data)
    return str(application.id), company.name


def _inject(db: Session, user: User, ai_client: AIClient) -> None:
    app.dependency_overrides[_get_service] = lambda: InterviewPrepService(
        db, user.id, ai_client=ai_client
    )


class TestServiceGenerate:
    def test_generates_with_explicit_company_and_title(
        self, db: Session, test_user: User
    ) -> None:
        service = InterviewPrepService(db, test_user.id, ai_client=_mock_client())
        pkg = service.create(
            InterviewPrepRequest(
                job_description=_JOB_DESCRIPTION,
                company_name="Acme",
                job_title="Senior Engineer",
                interview_type="Technical",
            )
        )
        assert pkg.company_name == "Acme"
        assert pkg.job_title == "Senior Engineer"
        assert pkg.interview_type == "Technical"
        assert pkg.result["checklist"] == ["Research the company", "Prepare questions"]
        assert pkg.provider == "mock"
        assert pkg.total_tokens > 0

    def test_derives_company_title_and_resume_from_application(
        self, db: Session, test_user: User
    ) -> None:
        resume_id = _create_resume(db, test_user)
        application_id, company_name = _create_application(
            db, test_user, resume_id=resume_id
        )
        service = InterviewPrepService(db, test_user.id, ai_client=_mock_client())

        pkg = service.create(
            InterviewPrepRequest(
                job_description=_JOB_DESCRIPTION, application_id=application_id
            )
        )
        assert pkg.company_name == company_name
        assert pkg.job_title == "Senior Engineer"
        # Falls back to the application's submitted resume.
        assert str(pkg.resume_id) == resume_id

    def test_tracks_ai_usage(self, db: Session, test_user: User) -> None:
        InterviewPrepService(db, test_user.id, ai_client=_mock_client()).create(
            InterviewPrepRequest(
                job_description=_JOB_DESCRIPTION,
                company_name="Acme",
                job_title="Engineer",
            )
        )
        usage = list(db.scalars(select(AIUsageRecord)))
        assert len(usage) == 1
        assert usage[0].feature == "interview_prep"
        assert usage[0].success is True

    def test_missing_company_and_title_raises(
        self, db: Session, test_user: User
    ) -> None:
        service = InterviewPrepService(db, test_user.id, ai_client=_mock_client())
        with pytest.raises(ValidationError):
            service.create(InterviewPrepRequest(job_description=_JOB_DESCRIPTION))


class TestGenerateApi:
    def test_returns_201_with_full_package(
        self, client: TestClient, db: Session, test_user: User
    ) -> None:
        _inject(db, test_user, _mock_client())
        response = client.post(
            "/api/v1/interview-prep/",
            json={
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Acme",
                "job_title": "Senior Engineer",
                "interview_type": "Technical",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["company_name"] == "Acme"
        assert body["result"]["company_overview"]["mission"]
        assert body["result"]["likely_questions"]["behavioral"]
        assert body["result"]["star_examples"][0]["situation"] == "S"
        assert body["result"]["checklist"]
        assert body["usage"]["total_tokens"] > 0
        assert body["usage"]["provider"] == "mock"

    def test_simulation_works_without_injection(
        self, client: TestClient, db: Session
    ) -> None:
        response = client.post(
            "/api/v1/interview-prep/",
            json={
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Globex",
                "job_title": "Backend Engineer",
                "interview_type": "Onsite",
            },
        )
        assert response.status_code == 201
        body = response.json()
        # Offline overview must disclaim the lack of external lookup.
        assert "external lookup" in body["result"]["company_overview"]["recent_news"]
        assert body["result"]["checklist"]

    def test_404_for_unknown_application(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/interview-prep/",
            json={
                "job_description": _JOB_DESCRIPTION,
                "application_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert response.status_code == 404

    def test_422_for_short_job_description(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/interview-prep/",
            json={
                "job_description": "short",
                "company_name": "Acme",
                "job_title": "Engineer",
            },
        )
        assert response.status_code == 422

    def test_invalid_ai_json_returns_502(
        self, client: TestClient, db: Session, test_user: User
    ) -> None:
        _inject(db, test_user, _mock_client(response="not json"))
        response = client.post(
            "/api/v1/interview-prep/",
            json={
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Acme",
                "job_title": "Engineer",
            },
        )
        assert response.status_code == 502


class TestHistoryApi:
    def test_list_reopen_and_delete(
        self, client: TestClient, db: Session, test_user: User
    ) -> None:
        _inject(db, test_user, _mock_client())
        created = client.post(
            "/api/v1/interview-prep/",
            json={
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Acme",
                "job_title": "Engineer",
            },
        ).json()

        listing = client.get("/api/v1/interview-prep/").json()
        assert listing["total"] == 1
        assert "result" not in listing["items"][0]  # lightweight list row

        reopened = client.get(f"/api/v1/interview-prep/{created['id']}").json()
        assert reopened["result"]["study_topics"]["languages"] == ["Python"]

        assert (
            client.delete(f"/api/v1/interview-prep/{created['id']}").status_code == 204
        )
        assert db.scalars(select(InterviewPrepPackage)).all() == []

    def test_filter_by_application(
        self, client: TestClient, db: Session, test_user: User
    ) -> None:
        _inject(db, test_user, _mock_client())
        client.post(
            "/api/v1/interview-prep/",
            json={
                "job_description": _JOB_DESCRIPTION,
                "company_name": "Acme",
                "job_title": "Engineer",
            },
        )
        other = "00000000-0000-0000-0000-000000000000"
        filtered = client.get(f"/api/v1/interview-prep/?application_id={other}").json()
        assert filtered["total"] == 0
