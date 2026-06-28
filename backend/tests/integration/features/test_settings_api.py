from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.companies.model import Company
from app.features.daily_briefing.model import Notification
from app.features.followups.model import FollowUp, FollowUpPriority, FollowUpStatus, FollowUpType
from app.features.interviews.model import Interview, InterviewStatus, InterviewType
from app.features.recruiters.model import Recruiter
from app.features.resumes.service import ResumeService
from app.features.tasks.model import Task, TaskPriority, TaskSource, TaskStatus
from app.features.users.model import User


def _login(client: TestClient, user: User, password: str = "StrongPass1") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["refresh_token"]


def test_settings_center_updates_account_timezone_and_notifications(
    client: TestClient, test_user: User
) -> None:
    response = client.patch(
        "/api/v1/settings/account",
        json={
            "full_name": "Settings User",
            "email": "settings-user@example.com",
            "timezone": "America/Phoenix",
            "notification_preferences": {
                "follow_up_reminders": True,
                "interview_reminders": False,
                "gmail_activity": True,
                "opportunity_alerts": False,
                "ai_insight_alerts": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["account"]["full_name"] == "Settings User"
    assert body["account"]["email"] == "settings-user@example.com"
    assert body["settings"]["timezone"] == "America/Phoenix"
    assert body["settings"]["notification_preferences"]["interview_reminders"] is False

    current = client.get("/api/v1/settings/").json()
    assert current["settings"]["timezone"] == "America/Phoenix"


def test_preferences_persist(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/settings/preferences",
        json={
            "theme": "dark",
            "default_dashboard_page": "daily_briefing",
            "default_notification_behavior": "important_only",
            "preferred_calendar_provider": "google",
            "preferred_ai_provider": "mock",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["theme"] == "dark"
    assert body["default_dashboard_page"] == "daily_briefing"
    assert body["default_notification_behavior"] == "important_only"
    assert body["preferred_calendar_provider"] == "google"
    assert body["preferred_ai_provider"] == "mock"

    current = client.get("/api/v1/settings/").json()
    assert current["settings"]["theme"] == "dark"


def test_password_change_verifies_current_password_and_invalidates_old_sessions(
    client: TestClient, test_user: User
) -> None:
    current_refresh = _login(client, test_user)
    old_refresh = _login(client, test_user)

    bad = client.post(
        "/api/v1/settings/security/change-password",
        json={
            "current_password": "wrong",
            "new_password": "NewStrongPass1",
            "current_refresh_token": current_refresh,
        },
    )
    assert bad.status_code == 401

    changed = client.post(
        "/api/v1/settings/security/change-password",
        json={
            "current_password": "StrongPass1",
            "new_password": "NewStrongPass1",
            "current_refresh_token": current_refresh,
        },
    )

    assert changed.status_code == 200
    assert changed.json()["password_changed"] is True
    assert (
        client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh}).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "StrongPass1"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "NewStrongPass1"},
        ).status_code
        == 200
    )


def test_sessions_list_current_and_sign_out_current(
    client: TestClient, test_user: User
) -> None:
    first = _login(client, test_user)
    _login(client, test_user)

    listing = client.post("/api/v1/settings/sessions", json={"refresh_token": first})
    current = client.post("/api/v1/settings/sessions/current", json={"refresh_token": first})
    signed_out = client.post(
        "/api/v1/settings/sessions/logout-current",
        json={"refresh_token": first},
    )

    assert listing.status_code == 200
    assert listing.json()["active_count"] >= 2
    assert any(item["is_current"] for item in listing.json()["items"])
    assert current.status_code == 200
    assert current.json()["is_current"] is True
    assert signed_out.status_code == 200
    assert signed_out.json()["revoked_count"] == 1
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": first}).status_code == 401


def test_export_returns_only_current_user_owned_records(
    client: TestClient, db: Session, test_user: User
) -> None:
    company = Company(name="ExportCo", industry="SaaS", user_id=test_user.id)
    hidden = Company(name="OtherCo", industry="Finance", user_id=_other_user(db).id)
    db.add_all([company, hidden])
    db.flush()
    recruiter = Recruiter(first_name="Alex", email="alex@export.test", user_id=test_user.id)
    application = JobApplication(
        company_id=company.id,
        job_title="Backend Engineer",
        status=ApplicationStatus.INTERVIEW.value,
        date_applied=date.today(),
        user_id=test_user.id,
    )
    db.add_all([recruiter, application])
    db.flush()
    db.add_all(
        [
            Interview(
                application_id=application.id,
                recruiter_id=recruiter.id,
                interview_type=InterviewType.TECHNICAL.value,
                scheduled_at=datetime.now(UTC) + timedelta(days=1),
                duration_minutes=45,
                status=InterviewStatus.SCHEDULED.value,
                user_id=test_user.id,
            ),
            FollowUp(
                application_id=application.id,
                recruiter_id=recruiter.id,
                title="Check in",
                followup_type=FollowUpType.RECRUITER_CHECKIN.value,
                status=FollowUpStatus.PENDING.value,
                priority=FollowUpPriority.HIGH.value,
                due_date=date.today(),
                user_id=test_user.id,
            ),
            Task(
                title="Tailor resume",
                status=TaskStatus.TODAY.value,
                priority=TaskPriority.HIGH.value,
                source=TaskSource.MANUAL.value,
                application_id=application.id,
                company_id=company.id,
                user_id=test_user.id,
            ),
            Notification(
                title="Follow-up due",
                message="Check in today.",
                category="follow_up",
                priority="high",
                dedupe_key="export-followup",
                user_id=test_user.id,
            ),
        ]
    )
    ResumeService(db, test_user.id).upload(
        file_name="resume.txt",
        content=b"Python backend engineer",
        name="Export Resume",
    )
    db.flush()

    response = client.get("/api/v1/settings/export")

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["name"] for item in data["companies"]] == ["ExportCo"]
    assert data["applications"][0]["job_title"] == "Backend Engineer"
    assert data["recruiters"][0]["email"] == "alex@export.test"
    assert data["interviews"]
    assert data["followups"]
    assert data["resumes"][0]["name"] == "Export Resume"
    assert data["tasks"][0]["title"] == "Tailor resume"
    assert data["notifications"][0]["title"] == "Follow-up due"
    assert all("user_id" not in item for section in data.values() for item in section)


def _other_user(db: Session) -> User:
    user = User(
        email="other-settings@example.com",
        hashed_password="not-used",
        full_name="Other User",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user
