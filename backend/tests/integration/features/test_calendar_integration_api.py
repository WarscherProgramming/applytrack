from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.calendar_integration.model import CalendarSyncEvent, CalendarSyncStatus
from app.features.companies.model import Company
from app.features.followups.model import FollowUp, FollowUpPriority, FollowUpStatus, FollowUpType
from app.features.interviews.model import Interview, InterviewStatus, InterviewType


def _seed_calendar_items(db: Session) -> tuple[Interview, FollowUp]:
    company = Company(name="Acme Calendar", industry="Healthcare", location="Remote")
    db.add(company)
    db.flush()
    application = JobApplication(
        company_id=company.id,
        job_title="Backend Platform Engineer",
        status=ApplicationStatus.INTERVIEW.value,
        date_applied=date.today(),
        source="Greenhouse",
    )
    db.add(application)
    db.flush()
    interview = Interview(
        application_id=application.id,
        interview_type=InterviewType.TECHNICAL.value,
        scheduled_at=datetime.now(UTC) + timedelta(days=2),
        duration_minutes=60,
        meeting_link="https://meet.example.test/calendar",
        status=InterviewStatus.SCHEDULED.value,
        notes="Review system design notes.",
    )
    followup = FollowUp(
        application_id=application.id,
        title="Send thank-you note",
        description="Thank the panel and ask about next steps.",
        followup_type=FollowUpType.THANK_YOU.value,
        status=FollowUpStatus.PENDING.value,
        priority=FollowUpPriority.HIGH.value,
        due_date=date.today() + timedelta(days=1),
    )
    db.add_all([interview, followup])
    db.flush()
    return interview, followup


def test_calendar_status_and_simulated_connect(client: TestClient) -> None:
    response = client.get("/api/v1/calendar-integration/status")

    assert response.status_code == 200
    body = response.json()
    assert {item["provider"] for item in body["connections"]} == {"google", "outlook"}
    assert all(item["status"] == "disconnected" for item in body["connections"])

    connect = client.post("/api/v1/calendar-integration/connect/google")

    assert connect.status_code == 200
    assert connect.json()["connected"] is True
    status = client.get("/api/v1/calendar-integration/status").json()
    google = next(item for item in status["connections"] if item["provider"] == "google")
    assert google["status"] == "connected"


def test_ics_export_includes_interviews_and_followups(
    client: TestClient, db: Session
) -> None:
    _seed_calendar_items(db)

    response = client.get("/api/v1/calendar-integration/ics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    body = response.text
    assert "BEGIN:VCALENDAR" in body
    assert "SUMMARY:Interview: Backend Platform Engineer" in body
    assert "SUMMARY:Follow-up: Send thank-you note" in body


def test_manual_sync_is_idempotent(client: TestClient, db: Session) -> None:
    _seed_calendar_items(db)
    client.post("/api/v1/calendar-integration/connect/google")

    first = client.post(
        "/api/v1/calendar-integration/sync",
        json={"provider": "google", "include_interviews": True, "include_followups": True},
    )
    second = client.post(
        "/api/v1/calendar-integration/sync",
        json={"provider": "google", "include_interviews": True, "include_followups": True},
    )

    assert first.status_code == 200
    assert first.json()["created"] == 2
    assert first.json()["synced_event_count"] == 2
    assert second.status_code == 200
    assert second.json()["skipped"] == 2
    assert second.json()["created"] == 0
    assert db.query(CalendarSyncEvent).count() == 2


def test_sync_updates_and_deletes_inactive_items(
    client: TestClient, db: Session
) -> None:
    interview, followup = _seed_calendar_items(db)
    client.post("/api/v1/calendar-integration/connect/google")
    client.post(
        "/api/v1/calendar-integration/sync",
        json={"provider": "google", "include_interviews": True, "include_followups": True},
    )

    interview.duration_minutes = 90
    followup.status = FollowUpStatus.COMPLETED.value
    db.flush()
    response = client.post(
        f"/api/v1/calendar-integration/interviews/{interview.id}/sync",
        json={"provider": "google"},
    )
    delete_response = client.post(
        "/api/v1/calendar-integration/sync",
        json={"provider": "google", "include_interviews": True, "include_followups": True},
    )

    assert response.status_code == 200
    assert response.json()["updated"] == 1
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] == 1
    deleted = (
        db.query(CalendarSyncEvent)
        .filter(CalendarSyncEvent.item_id == str(followup.id))
        .one()
    )
    assert deleted.status == CalendarSyncStatus.DELETED.value
