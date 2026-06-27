import json
from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.mock_provider import MockProvider
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.career_copilot.router import _get_service
from app.features.career_copilot.service import CareerCopilotService
from app.features.companies.model import Company
from app.features.followups.model import FollowUp
from app.features.gmail.models import EmailMessage, GmailAccount
from app.features.interviews.model import Interview
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.model import Resume
from app.main import app


def _mock_client(response: str | None = None) -> AIClient:
    payload = response or json.dumps(
        {
            "executive_summary": "Start with overdue follow-ups, then prepare for the interview.",
            "ai_recommendations": [
                "Clear overdue follow-ups",
                "Prepare your Kubernetes story",
            ],
            "skill_focus": "Kubernetes is the strongest skill signal today.",
            "resume_recommendation": "Use the Backend Resume baseline.",
            "interview_preparation_reminder": "Review system design notes before the interview.",
            "follow_up_reminder": "Send the overdue recruiter check-in first.",
            "caveats": [],
        }
    )
    return AIClient(MockProvider(default_response=payload), default_model="mock-model")


def _inject_client(db: Session, client: AIClient | None = None) -> None:
    app.dependency_overrides[_get_service] = lambda: CareerCopilotService(
        db, ai_client=client or _mock_client()
    )


def _seed_copilot_data(db: Session) -> None:
    now = datetime.now(UTC)
    today = now.date()

    company = Company(name="Acme Health", industry="Healthcare", location="Remote")
    db.add(company)
    db.flush()

    resume = Resume(
        name="Backend Resume",
        file_name="resume.txt",
        storage_path="resumes/backend.txt",
        version=1,
    )
    db.add(resume)
    db.flush()

    application = JobApplication(
        company_id=company.id,
        job_title="Backend Engineer",
        status=ApplicationStatus.INTERVIEW.value,
        date_applied=date(2026, 1, 1),
        resume_id=resume.id,
    )
    db.add(application)
    db.flush()

    db.add_all(
        [
            FollowUp(
                application_id=application.id,
                title="Email recruiter",
                followup_type="recruiter_checkin",
                status="pending",
                priority="high",
                due_date=today - timedelta(days=1),
            ),
            FollowUp(
                application_id=application.id,
                title="Send thank-you note",
                followup_type="thank_you",
                status="pending",
                priority="medium",
                due_date=today,
            ),
            Interview(
                application_id=application.id,
                interview_type="technical",
                scheduled_at=now + timedelta(days=1),
                duration_minutes=45,
                status="scheduled",
                notes="System design",
            ),
        ]
    )

    account = GmailAccount(email_address="jobseeker@example.com", status="connected")
    db.add(account)
    db.flush()
    db.add(
        EmailMessage(
            account_id=account.id,
            message_id="m1",
            thread_id="t1",
            subject="Next steps",
            sender="recruiting@acme.test",
            recipients=["jobseeker@example.com"],
            sent_at=now - timedelta(hours=3),
            direction="inbound",
            labels=["INBOX"],
            attachments=[],
            application_id=application.id,
            company_id=company.id,
            match_confidence=0.9,
            match_reason="company domain",
        )
    )
    db.add(
        ResumeMatchAnalysis(
            resume_id=resume.id,
            resume_name="Backend Resume (v1)",
            job_description="Backend Python role with FastAPI, Kubernetes, Docker, and AWS.",
            overall_match_score=80,
            result={"missing_skills": ["Kubernetes"], "interview_topics": ["System design"]},
            provider="mock",
            model="mock-model",
        )
    )
    db.flush()


def test_daily_briefing_aggregates_priorities_and_ai(
    client: TestClient, db: Session
) -> None:
    _seed_copilot_data(db)
    _inject_client(db)

    response = client.get("/api/v1/career-copilot/daily")

    assert response.status_code == 200
    body = response.json()
    assert body["today_metrics"]["followups_due_today"] == 1
    assert body["today_metrics"]["overdue_followups"] == 1
    assert body["today_metrics"]["upcoming_interviews"] == 1
    assert body["today_metrics"]["recent_emails"] == 1
    assert body["briefing"]["top_priorities"][0]["priority"] == "urgent"
    assert body["briefing"]["ai_recommendations"][0] == "Clear overdue follow-ups"
    assert body["ai_insight_panel"]["available"] is True
    assert body["recent_gmail_activity"][0]["subject"] == "Next steps"
    assert body["upcoming_interviews"][0]["title"] == "Backend Engineer"


def test_ai_failure_returns_deterministic_briefing(
    client: TestClient, db: Session
) -> None:
    _seed_copilot_data(db)
    _inject_client(db, _mock_client(response="not json"))

    response = client.get("/api/v1/career-copilot/daily")

    assert response.status_code == 200
    body = response.json()
    assert body["ai_insight_panel"]["available"] is False
    assert body["briefing"]["top_priorities"]
    assert "AI narrative unavailable" in body["ai_insight_panel"]["caveats"][-1]


def test_empty_briefing_is_explicit(client: TestClient) -> None:
    response = client.get("/api/v1/career-copilot/daily")

    assert response.status_code == 200
    body = response.json()
    assert body["today_metrics"]["active_applications"] == 0
    assert body["ai_insight_panel"]["available"] is False
    assert body["briefing"]["top_priorities"][0]["title"] == "Add fresh job-search activity"

