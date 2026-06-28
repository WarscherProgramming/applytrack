from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.companies.model import Company
from app.features.followups.model import FollowUp, FollowUpPriority, FollowUpStatus, FollowUpType
from app.features.gmail.models import EmailMessage, GmailAccount
from app.features.interviews.model import Interview, InterviewStatus, InterviewType
from app.features.tasks.model import Task
from app.features.users.model import User


def _seed_context(
    db: Session, user: User
) -> tuple[Company, JobApplication, FollowUp, Interview]:
    company = Company(
        name="TaskCo", industry="Healthcare", location="Remote", user_id=user.id
    )
    db.add(company)
    db.flush()
    application = JobApplication(
        company_id=company.id,
        job_title="Backend Engineer",
        status=ApplicationStatus.INTERVIEW.value,
        source="Opportunity Discovery: greenhouse",
        user_id=user.id,
    )
    db.add(application)
    db.flush()
    followup = FollowUp(
        application_id=application.id,
        title="Check in with recruiter",
        description="Ask whether the team has feedback.",
        followup_type=FollowUpType.RECRUITER_CHECKIN.value,
        status=FollowUpStatus.PENDING.value,
        priority=FollowUpPriority.URGENT.value,
        due_date=date.today() - timedelta(days=2),
        user_id=user.id,
    )
    interview = Interview(
        application_id=application.id,
        interview_type=InterviewType.TECHNICAL.value,
        scheduled_at=datetime.now(UTC) + timedelta(days=2),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED.value,
        notes="Review API design.",
        user_id=user.id,
    )
    db.add_all([followup, interview])
    db.flush()
    return company, application, followup, interview


def _seed_unread_email(
    db: Session, user: User, company: Company, application: JobApplication
) -> None:
    account = GmailAccount(email_address="jobseeker@example.test", user_id=user.id)
    db.add(account)
    db.flush()
    db.add(
        EmailMessage(
            account_id=account.id,
            message_id="task-msg-1",
            thread_id="task-thread-1",
            subject="Recruiter update",
            sender="recruiter@taskco.test",
            recipients=["jobseeker@example.test"],
            sent_at=datetime.now(UTC) - timedelta(hours=1),
            direction="inbound",
            labels=["INBOX", "UNREAD"],
            attachments=[],
            company_id=company.id,
            application_id=application.id,
            match_confidence=0.9,
            match_reason="recruiting email",
            user_id=user.id,
        )
    )
    db.flush()


def test_manual_task_lifecycle(
    client: TestClient, db: Session, test_user: User
) -> None:
    company, application, _, _ = _seed_context(db, test_user)

    created = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Tailor resume",
            "description": "Use the backend version.",
            "priority": "high",
            "status": "backlog",
            "source": "manual",
            "application_id": str(application.id),
            "company_id": str(company.id),
            "due_date": date.today().isoformat(),
        },
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress", "priority": "urgent"},
    )
    completed = client.post(f"/api/v1/tasks/{task_id}/complete")
    dismissed = client.post(f"/api/v1/tasks/{task_id}/dismiss")
    deleted = client.delete(f"/api/v1/tasks/{task_id}")

    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"
    assert updated.json()["priority"] == "urgent"
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["completed_at"] is not None
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"
    assert deleted.status_code == 204


def test_generated_tasks_are_idempotent(
    client: TestClient, db: Session, test_user: User
) -> None:
    company, application, followup, interview = _seed_context(db, test_user)
    _seed_unread_email(db, test_user, company, application)

    followups = client.post("/api/v1/tasks/generate/overdue-followups")
    interviews = client.post("/api/v1/tasks/generate/upcoming-interviews")
    emails = client.post("/api/v1/tasks/generate/recruiter-emails")
    second_followups = client.post("/api/v1/tasks/generate/overdue-followups")

    assert followups.status_code == 200
    assert followups.json()["created"] == 1
    assert followups.json()["items"][0]["followup_id"] == str(followup.id)
    assert followups.json()["items"][0]["priority"] == "urgent"
    assert interviews.status_code == 200
    assert interviews.json()["created"] == 1
    assert interviews.json()["items"][0]["interview_id"] == str(interview.id)
    assert emails.status_code == 200
    assert emails.json()["created"] == 1
    assert emails.json()["items"][0]["source"] == "gmail"
    assert second_followups.status_code == 200
    assert second_followups.json()["created"] == 0
    assert second_followups.json()["updated"] == 1
    assert db.query(Task).count() == 3


def test_task_filters_and_daily_briefing_generation(
    client: TestClient, db: Session, test_user: User
) -> None:
    _seed_context(db, test_user)

    generated = client.post("/api/v1/tasks/generate/daily-briefing")
    today = client.get("/api/v1/tasks/?status=today")
    daily = client.get("/api/v1/tasks/?source=daily_briefing")

    assert generated.status_code == 200
    assert generated.json()["created"] >= 1
    assert today.status_code == 200
    assert today.json()["total"] >= 1
    assert daily.status_code == 200
    assert all(item["source"] == "daily_briefing" for item in daily.json()["items"])
