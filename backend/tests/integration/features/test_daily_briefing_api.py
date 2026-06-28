import json
from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.mock_provider import MockProvider
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.companies.model import Company
from app.features.daily_briefing.router import _get_service
from app.features.daily_briefing.service import DailyBriefingService
from app.features.followups.model import FollowUp, FollowUpPriority, FollowUpStatus, FollowUpType
from app.features.gmail.models import EmailMessage, GmailAccount
from app.features.interviews.model import Interview, InterviewStatus, InterviewType
from app.features.users.model import User
from app.main import app


def _mock_client(response: str | None = None) -> AIClient:
    payload = response or json.dumps(
        {
            "morning_summary": (
                "Clear overdue follow-ups, prep for the interview, and review "
                "recruiter mail."
            ),
            "recommendations": [
                "Send the overdue follow-up.",
                "Prepare for the technical interview.",
            ],
            "caveats": [],
        }
    )
    return AIClient(MockProvider(default_response=payload), default_model="mock-model")


def _inject_client(db: Session, user: User, client: AIClient | None = None) -> None:
    app.dependency_overrides[_get_service] = lambda: DailyBriefingService(
        db, user.id, ai_client=client or _mock_client()
    )


def _seed_data(db: Session, user: User) -> None:
    company = Company(
        name="Acme Health",
        industry="Healthcare",
        location="Remote",
        user_id=user.id,
    )
    db.add(company)
    db.flush()
    application = JobApplication(
        company_id=company.id,
        job_title="Backend Platform Engineer",
        status=ApplicationStatus.INTERVIEW.value,
        source="Opportunity Discovery: greenhouse",
        job_link="https://jobs.example.test/backend",
        user_id=user.id,
    )
    db.add(application)
    db.flush()

    today = date.today()
    db.add_all(
        [
            FollowUp(
                application_id=application.id,
                title="Send thank-you note",
                followup_type=FollowUpType.THANK_YOU.value,
                status=FollowUpStatus.PENDING.value,
                priority=FollowUpPriority.HIGH.value,
                due_date=today,
                user_id=user.id,
            ),
            FollowUp(
                application_id=application.id,
                title="Check recruiter response",
                followup_type=FollowUpType.RECRUITER_CHECKIN.value,
                status=FollowUpStatus.PENDING.value,
                priority=FollowUpPriority.URGENT.value,
                due_date=today - timedelta(days=2),
                user_id=user.id,
            ),
            Interview(
                application_id=application.id,
                interview_type=InterviewType.TECHNICAL.value,
                scheduled_at=datetime.now(UTC) + timedelta(days=1),
                duration_minutes=60,
                status=InterviewStatus.SCHEDULED.value,
                meeting_link="https://meet.example.test",
                user_id=user.id,
            ),
        ]
    )
    account = GmailAccount(email_address="jobseeker@example.test", user_id=user.id)
    db.add(account)
    db.flush()
    db.add(
        EmailMessage(
            account_id=account.id,
            message_id="msg-1",
            thread_id="thread-1",
            subject="Recruiter follow up",
            sender="recruiter@acme.test",
            recipients=["jobseeker@example.test"],
            sent_at=datetime.now(UTC) - timedelta(hours=2),
            direction="inbound",
            labels=["INBOX"],
            attachments=[],
            company_id=company.id,
            application_id=application.id,
            match_confidence=0.95,
            match_reason="recruiting email",
            user_id=user.id,
        )
    )
    db.flush()


def test_daily_briefing_generates_sections_and_notifications(
    client: TestClient, db: Session, test_user: User
) -> None:
    _seed_data(db, test_user)
    _inject_client(db, test_user)

    response = client.post("/api/v1/daily-briefing/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["followups_due_today"][0]["title"] == "Send thank-you note"
    assert body["overdue_followups"][0]["title"] == "Check recruiter response"
    assert body["upcoming_interviews"]
    assert body["new_recruiter_emails"][0]["sender"] == "recruiter@acme.test"
    assert body["newly_discovered_opportunities"][0]["title"] == "Backend Platform Engineer"
    assert body["ai_recommendations"] == [
        "Send the overdue follow-up.",
        "Prepare for the technical interview.",
    ]
    assert body["unread_notification_count"] >= 4

    notifications = client.get("/api/v1/daily-briefing/notifications").json()
    categories = {item["category"] for item in notifications["items"]}
    assert {"follow_up", "interview", "gmail", "opportunity"} <= categories


def test_notification_state_updates(
    client: TestClient, db: Session, test_user: User
) -> None:
    _seed_data(db, test_user)
    _inject_client(db, test_user)
    client.post("/api/v1/daily-briefing/refresh")
    notification = client.get("/api/v1/daily-briefing/notifications").json()["items"][0]

    response = client.patch(
        f"/api/v1/daily-briefing/notifications/{notification['id']}",
        json={"is_read": True, "is_pinned": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_read"] is True
    assert body["is_pinned"] is True

    pinned = client.get("/api/v1/daily-briefing/notifications?pinned_only=true").json()
    assert pinned["pinned_count"] == 1
    assert pinned["items"][0]["id"] == notification["id"]

    dismiss = client.patch(
        f"/api/v1/daily-briefing/notifications/{notification['id']}",
        json={"is_dismissed": True},
    )
    assert dismiss.status_code == 200
    client.post("/api/v1/daily-briefing/refresh")
    active = client.get("/api/v1/daily-briefing/notifications").json()
    assert notification["id"] not in {item["id"] for item in active["items"]}


def test_ai_failure_keeps_deterministic_briefing(
    client: TestClient, db: Session, test_user: User
) -> None:
    _seed_data(db, test_user)
    _inject_client(db, test_user, _mock_client(response="not json"))

    response = client.post("/api/v1/daily-briefing/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["ai_narrative"]["available"] is False
    assert body["prioritized_actions"]
    assert "AI narrative unavailable" in body["ai_narrative"]["caveats"][-1]
