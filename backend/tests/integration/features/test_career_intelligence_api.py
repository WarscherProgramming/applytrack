import json
from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.mock_provider import MockProvider
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.career_intelligence.router import _get_service
from app.features.career_intelligence.service import CareerIntelligenceService
from app.features.companies.model import Company
from app.features.cover_letters.model import CoverLetter
from app.features.gmail.models import EmailMessage, GmailAccount
from app.features.interviews.model import Interview
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.model import Resume
from app.features.users.model import User
from app.main import app


def _mock_client() -> AIClient:
    payload = {
        "executive_summary": "Your backend-focused applications are producing responses.",
        "recommendations": [
            {
                "title": "Emphasize Kubernetes",
                "detail": "Kubernetes appears frequently in stored job descriptions.",
                "evidence": "Observed in computed skill counts.",
            }
        ],
        "caveats": [],
    }
    return AIClient(
        MockProvider(default_response=json.dumps(payload)), default_model="mock-model"
    )


def _inject_client(db: Session, user: User) -> None:
    app.dependency_overrides[_get_service] = lambda: CareerIntelligenceService(
        db, user.id, ai_client=_mock_client()
    )


def _seed_history(db: Session, user: User) -> None:
    acme = Company(
        name="Acme Health",
        industry="Healthcare",
        location="Remote",
        user_id=user.id,
    )
    cloud = Company(
        name="CloudWorks", industry="SaaS", location="Denver", user_id=user.id
    )
    db.add_all([acme, cloud])
    db.flush()

    resume = Resume(
        name="Backend Resume",
        file_name="resume.txt",
        storage_path="resumes/1.txt",
        version=1,
        user_id=user.id,
    )
    cover = CoverLetter(
        name="Backend Cover Letter",
        file_name="cover.md",
        storage_path="cover_letters/1.md",
        version=1,
        user_id=user.id,
    )
    db.add_all([resume, cover])
    db.flush()

    app_one = JobApplication(
        company_id=acme.id,
        job_title="Backend Engineer",
        status=ApplicationStatus.INTERVIEW.value,
        date_applied=date(2026, 1, 1),
        location="Remote",
        resume_id=resume.id,
        cover_letter_id=cover.id,
        user_id=user.id,
    )
    app_two = JobApplication(
        company_id=cloud.id,
        job_title="Senior Platform Engineer",
        status=ApplicationStatus.GHOSTED.value,
        date_applied=date(2026, 1, 10),
        location="Denver",
        user_id=user.id,
    )
    db.add_all([app_one, app_two])
    db.flush()

    account = GmailAccount(
        email_address="jobseeker@example.com", status="connected", user_id=user.id
    )
    db.add(account)
    db.flush()
    db.add(
        EmailMessage(
            account_id=account.id,
            message_id="m1",
            thread_id="t1",
            subject="Interview request",
            sender="recruiting@acme.test",
            recipients=["jobseeker@example.com"],
            sent_at=datetime(2026, 1, 4, 15, tzinfo=UTC),
            direction="inbound",
            labels=["INBOX"],
            attachments=[],
            application_id=app_one.id,
            company_id=acme.id,
            match_confidence=0.9,
            user_id=user.id,
        )
    )
    db.add(
        Interview(
            application_id=app_one.id,
            interview_type="technical",
            scheduled_at=datetime(2026, 1, 8, 18, tzinfo=UTC),
            duration_minutes=45,
            status="completed",
            notes="System design and API discussion",
            user_id=user.id,
        )
    )
    db.add(
        ResumeMatchAnalysis(
            resume_id=resume.id,
            resume_name="Backend Resume (v1)",
            job_description=(
                "Backend Python role requiring FastAPI, PostgreSQL, Docker, "
                "Kubernetes, and AWS."
            ),
            overall_match_score=81,
            result={
                "missing_skills": ["Kubernetes"],
                "interview_topics": ["System design"],
            },
            provider="mock",
            model="mock-model",
            user_id=user.id,
        )
    )
    db.flush()


def test_dashboard_calculates_core_metrics(
    client: TestClient, db: Session, test_user: User
) -> None:
    _seed_history(db, test_user)
    _inject_client(db, test_user)

    response = client.get("/api/v1/career-intelligence/")

    assert response.status_code == 200
    body = response.json()
    metrics = body["application_metrics"]
    assert metrics["total_applications"] == 2
    assert metrics["active_applications"] == 1
    assert metrics["response_rate"]["value"] == 50.0
    assert metrics["interview_rate"]["value"] == 50.0
    assert metrics["ghost_rate"]["value"] == 50.0
    assert metrics["average_days_until_first_response"] == 3.0
    assert metrics["average_interview_count_per_application"] == 0.5
    assert body["skill_intelligence"]["job_description_count"] == 1
    assert body["skill_intelligence"]["most_requested_skills"][0]["name"] == "Python"
    assert body["resume_insights"]["highest_interview_rate"]["name"] == "Backend Resume"
    assert body["ai_recommendations"]["available"] is True
    assert body["ai_recommendations"]["recommendations"][0]["title"] == "Emphasize Kubernetes"


def test_date_filter_and_comparison(
    client: TestClient, db: Session, test_user: User
) -> None:
    _seed_history(db, test_user)
    _inject_client(db, test_user)

    response = client.get(
        "/api/v1/career-intelligence/"
        "?date_from=2026-01-01&date_to=2026-01-05"
        "&compare_date_from=2026-01-06&compare_date_to=2026-01-31"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["application_metrics"]["total_applications"] == 1
    assert body["comparison"]["metrics"][0]["name"] == "Total applications"
    assert body["comparison"]["metrics"][0]["previous"] == 1.0


def test_empty_dashboard_is_explicit(client: TestClient) -> None:
    response = client.get("/api/v1/career-intelligence/")

    assert response.status_code == 200
    body = response.json()
    assert body["application_metrics"]["total_applications"] == 0
    assert body["ai_recommendations"]["available"] is False
    assert body["ai_recommendations"]["recommendations"][0]["title"] == "Add more tracked outcomes"

