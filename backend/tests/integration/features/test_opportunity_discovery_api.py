import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.mock_provider import MockProvider
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.companies.model import Company
from app.features.cover_letters.service import CoverLetterService
from app.features.opportunity_discovery.providers.base import JobProvider, ProviderFetchRequest
from app.features.opportunity_discovery.providers.greenhouse import GreenhouseProvider
from app.features.opportunity_discovery.router import _get_service
from app.features.opportunity_discovery.schemas import (
    JobProviderName,
    NormalizedJobPosting,
    SkillTag,
    WorkMode,
)
from app.features.opportunity_discovery.service import OpportunityDiscoveryService
from app.features.resumes.service import ResumeService
from app.features.users.model import User
from app.main import app


class FakeProvider(JobProvider):
    name = JobProviderName.GREENHOUSE

    def fetch(self, request: ProviderFetchRequest) -> list[NormalizedJobPosting]:
        return [
            NormalizedJobPosting(
                id="fake-1",
                provider=self.name,
                provider_job_id="1",
                company="Acme Health",
                title="Backend Platform Engineer",
                location="Remote",
                salary="$150,000 - $180,000",
                employment_type="Full-time",
                work_mode=WorkMode.REMOTE,
                job_url="https://jobs.example.test/backend",
                description="Python FastAPI Kubernetes Terraform PostgreSQL AWS mentoring",
                industry="Healthcare",
                skills=[
                    SkillTag(name="Python", category="Programming Languages"),
                    SkillTag(name="FastAPI", category="Frameworks"),
                    SkillTag(name="Kubernetes", category="DevOps"),
                    SkillTag(name="Terraform", category="DevOps"),
                    SkillTag(name="PostgreSQL", category="Databases"),
                ],
            )
        ]


def _mock_client(response: str | None = None) -> AIClient:
    payload = response or json.dumps(
        {
            "summary": "Strong backend platform fit with two infrastructure gaps.",
            "score_explanation": "The score is driven by Python and PostgreSQL overlap.",
            "next_steps": ["Run a deeper resume match.", "Prepare Kubernetes evidence."],
            "cautions": [],
        }
    )
    return AIClient(MockProvider(default_response=payload), default_model="mock-model")


def _inject_service(db: Session, user: User, client: AIClient | None = None) -> None:
    app.dependency_overrides[_get_service] = lambda: OpportunityDiscoveryService(
        db,
        user.id,
        providers={JobProviderName.GREENHOUSE: FakeProvider()},
        ai_client=client or _mock_client(),
    )


def _seed_documents_and_history(db: Session, user: User):
    company = Company(
        name="Acme Health",
        industry="Healthcare",
        location="Remote",
        user_id=user.id,
    )
    db.add(company)
    db.flush()
    db.add(
        JobApplication(
            company_id=company.id,
            job_title="Backend Engineer",
            status=ApplicationStatus.INTERVIEW.value,
            user_id=user.id,
        )
    )
    resume = ResumeService(db, user.id).upload(
        file_name="resume.txt",
        content=b"Python backend engineer with FastAPI, PostgreSQL, Docker, and AWS.",
        name="Backend Resume",
    )
    cover_letter = CoverLetterService(db, user.id).upload(
        file_name="cover.txt",
        content=b"Dear Acme Health, I am excited about backend platform work.",
        name="Acme Backend Cover",
    )
    db.flush()
    return resume, cover_letter


def test_search_scores_provider_jobs_and_ai_explains(
    client: TestClient, db: Session, test_user: User
) -> None:
    resume, cover_letter = _seed_documents_and_history(db, test_user)
    _inject_service(db, test_user)

    response = client.post(
        "/api/v1/opportunity-discovery/search",
        json={
            "providers": ["greenhouse"],
            "greenhouse_boards": ["fake-board"],
            "query": "backend",
            "resume_id": str(resume.id),
            "preferred_location": "Remote",
            "preferred_job_type": "Full-time",
            "preferred_industry": "Healthcare",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["posting"]["company"] == "Acme Health"
    assert item["score"]["overall_match_percent"] > 50
    assert item["score"]["recommended_resume_id"] == str(resume.id)
    assert item["score"]["suggested_cover_letter_id"] == str(cover_letter.id)
    assert "Kubernetes" in item["score"]["top_missing_skills"]
    assert item["ai_explanation"]["available"] is True
    assert body["top_technologies"][0]["name"] in {"Python", "FastAPI"}


def test_save_opportunity_creates_draft_application(
    client: TestClient, db: Session, test_user: User
) -> None:
    resume, cover_letter = _seed_documents_and_history(db, test_user)
    _inject_service(db, test_user)
    search = client.post(
        "/api/v1/opportunity-discovery/search",
        json={"greenhouse_boards": ["fake-board"]},
    ).json()
    posting = search["items"][0]["posting"]

    response = client.post(
        "/api/v1/opportunity-discovery/save",
        json={
            "posting": posting,
            "resume_id": str(resume.id),
            "cover_letter_id": str(cover_letter.id),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["application"]["job_title"] == "Backend Platform Engineer"
    assert body["application"]["status"] == "draft"
    assert body["application"]["source"] == "Opportunity Discovery: greenhouse"
    assert body["application"]["resume_id"] == str(resume.id)


def test_ai_failure_returns_deterministic_explanation(
    client: TestClient, db: Session, test_user: User
) -> None:
    _seed_documents_and_history(db, test_user)
    _inject_service(db, test_user, _mock_client(response="not json"))

    response = client.post(
        "/api/v1/opportunity-discovery/search",
        json={"greenhouse_boards": ["fake-board"]},
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["ai_explanation"]["available"] is False
    assert "AI explanation unavailable" in item["ai_explanation"]["cautions"][-1]


def test_greenhouse_provider_normalizes_public_api_payload(monkeypatch) -> None:
    def fake_json(url: str):
        assert "greenhouse.io" in url
        return {
            "name": "Example Co",
            "jobs": [
                {
                    "id": 123,
                    "title": "Python Engineer",
                    "location": {"name": "Remote US"},
                    "absolute_url": "https://example.test/jobs/123",
                    "updated_at": "2026-01-01T12:00:00Z",
                    "content": "<p>Build APIs with Python, Django, and Kubernetes.</p>",
                }
            ],
        }

    monkeypatch.setattr(
        "app.features.opportunity_discovery.providers.greenhouse.get_json",
        fake_json,
    )

    jobs = GreenhouseProvider().fetch(ProviderFetchRequest(source="example"))

    assert len(jobs) == 1
    assert jobs[0].company == "Example Co"
    assert jobs[0].work_mode == WorkMode.REMOTE
    assert {skill.name for skill in jobs[0].skills} >= {"Python", "Django", "Kubernetes"}
