import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.mock_provider import MockProvider
from app.ai.usage_tracker import AIUsageRecord
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resume_match.router import _get_service
from app.features.resume_match.schema import ResumeMatchCreate
from app.features.resume_match.service import ResumeMatchService
from app.features.resumes.service import ResumeService
from app.main import app

# A valid ResumeMatchResult the mock provider returns for every call.
_RESULT_JSON = json.dumps(
    {
        "overall_match_score": 82,
        "strengths": ["Strong Python background", "REST API experience"],
        "weaknesses": ["Limited Kubernetes exposure"],
        "missing_skills": ["Kubernetes", "Terraform"],
        "recommended_keywords": ["FastAPI", "CI/CD"],
        "recommended_resume_changes": ["Quantify impact with metrics"],
        "interview_topics": ["System design", "Database indexing"],
    }
)

_JOB_DESCRIPTION = (
    "We are hiring a senior backend engineer with strong Python, FastAPI, and "
    "PostgreSQL experience. Kubernetes and Terraform are a plus."
)


def _mock_client(response: str = _RESULT_JSON) -> AIClient:
    return AIClient(
        MockProvider(default_response=response), default_model="mock-model"
    )


def _create_resume(db: Session, *, content: bytes = b"Experienced Python engineer.") -> str:
    resume = ResumeService(db).upload(
        file_name="resume.txt", content=content, name="My Resume"
    )
    return str(resume.id)


def _inject_client(db: Session, ai_client: AIClient) -> None:
    """Override the API's service dependency with a controlled AI client.

    Cleared automatically by the `client` fixture's dependency_overrides.clear().
    """
    app.dependency_overrides[_get_service] = lambda: ResumeMatchService(
        db, ai_client=ai_client
    )


class TestServiceDirect:
    def test_runs_and_persists_analysis(self, db: Session) -> None:
        resume_id = _create_resume(db)
        service = ResumeMatchService(db, ai_client=_mock_client())

        analysis = service.create(
            ResumeMatchCreate(resume_id=resume_id, job_description=_JOB_DESCRIPTION)
        )

        assert analysis.overall_match_score == 82
        assert analysis.resume_name == "My Resume (v1)"
        assert analysis.provider == "mock"
        assert analysis.result["missing_skills"] == ["Kubernetes", "Terraform"]

    def test_tracks_ai_usage(self, db: Session) -> None:
        resume_id = _create_resume(db)
        ResumeMatchService(db, ai_client=_mock_client()).create(
            ResumeMatchCreate(resume_id=resume_id, job_description=_JOB_DESCRIPTION)
        )

        usage = list(db.scalars(select(AIUsageRecord)))
        assert len(usage) == 1
        assert usage[0].feature == "resume_match"
        assert usage[0].success is True

    def test_unsupported_resume_format_raises(self, db: Session) -> None:
        resume = ResumeService(db).upload(
            file_name="resume.doc", content=b"\xd0\xcf binary", name="Legacy"
        )
        service = ResumeMatchService(db, ai_client=_mock_client())
        from app.features.resume_match.text_extraction import ResumeTextExtractionError

        with pytest.raises(ResumeTextExtractionError):
            service.create(
                ResumeMatchCreate(
                    resume_id=resume.id, job_description=_JOB_DESCRIPTION
                )
            )


class TestRunAnalysisApi:
    def test_returns_201_with_full_result(
        self, client: TestClient, db: Session
    ) -> None:
        resume_id = _create_resume(db)
        _inject_client(db, _mock_client())

        response = client.post(
            "/api/v1/resume-match/",
            json={"resume_id": resume_id, "job_description": _JOB_DESCRIPTION},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["overall_match_score"] == 82
        assert body["resume_name"] == "My Resume (v1)"
        assert body["result"]["strengths"]
        assert body["result"]["interview_topics"]
        assert body["provider"] == "mock"

    def test_simulation_works_without_injection(
        self, client: TestClient, db: Session
    ) -> None:
        # No injected client: the service falls back to mock simulation (no API
        # key in tests), proving the default local-dev path works end to end.
        resume_id = _create_resume(db)
        response = client.post(
            "/api/v1/resume-match/",
            json={"resume_id": resume_id, "job_description": _JOB_DESCRIPTION},
        )
        assert response.status_code == 201
        body = response.json()
        assert 0 <= body["overall_match_score"] <= 100
        assert isinstance(body["result"]["recommended_keywords"], list)
        assert body["result"]["interview_topics"]

    def test_404_for_unknown_resume(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/resume-match/",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "job_description": _JOB_DESCRIPTION,
            },
        )
        assert response.status_code == 404

    def test_422_for_short_job_description(
        self, client: TestClient, db: Session
    ) -> None:
        resume_id = _create_resume(db)
        response = client.post(
            "/api/v1/resume-match/",
            json={"resume_id": resume_id, "job_description": "too short"},
        )
        assert response.status_code == 422

    def test_invalid_ai_json_returns_502(
        self, client: TestClient, db: Session
    ) -> None:
        resume_id = _create_resume(db)
        _inject_client(db, _mock_client(response="this is not json"))

        response = client.post(
            "/api/v1/resume-match/",
            json={"resume_id": resume_id, "job_description": _JOB_DESCRIPTION},
        )
        # AIResponseError -> 502 via the global handler.
        assert response.status_code == 502


class TestHistoryApi:
    def test_list_and_reopen(self, client: TestClient, db: Session) -> None:
        resume_id = _create_resume(db)
        _inject_client(db, _mock_client())

        created = client.post(
            "/api/v1/resume-match/",
            json={"resume_id": resume_id, "job_description": _JOB_DESCRIPTION},
        ).json()

        listing = client.get("/api/v1/resume-match/").json()
        assert listing["total"] == 1
        item = listing["items"][0]
        assert item["overall_match_score"] == 82
        assert item["job_description_preview"]
        # The lightweight item must not carry the full result payload.
        assert "result" not in item

        reopened = client.get(f"/api/v1/resume-match/{created['id']}").json()
        assert reopened["id"] == created["id"]
        assert reopened["result"]["missing_skills"] == ["Kubernetes", "Terraform"]

    def test_filter_by_resume(self, client: TestClient, db: Session) -> None:
        resume_id = _create_resume(db)
        _inject_client(db, _mock_client())
        client.post(
            "/api/v1/resume-match/",
            json={"resume_id": resume_id, "job_description": _JOB_DESCRIPTION},
        )
        other = "00000000-0000-0000-0000-000000000000"
        filtered = client.get(f"/api/v1/resume-match/?resume_id={other}").json()
        assert filtered["total"] == 0

    def test_delete(self, client: TestClient, db: Session) -> None:
        resume_id = _create_resume(db)
        _inject_client(db, _mock_client())
        created = client.post(
            "/api/v1/resume-match/",
            json={"resume_id": resume_id, "job_description": _JOB_DESCRIPTION},
        ).json()

        assert client.delete(f"/api/v1/resume-match/{created['id']}").status_code == 204
        assert client.get(f"/api/v1/resume-match/{created['id']}").status_code == 404
        assert db.scalars(select(ResumeMatchAnalysis)).all() == []
