from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.companies.model import Company
from app.features.users.model import User


def _create_user(db: Session, email_prefix: str) -> User:
    user = User(
        email=f"{email_prefix}-{uuid4()}@example.com",
        hashed_password=hash_password("StrongPass1"),
        full_name="Other User",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_company_lists_and_direct_access_are_scoped(
    client: TestClient, db: Session, test_user: User
) -> None:
    other_user = _create_user(db, "other-user")
    visible = Company(name="VisibleCo", industry="SaaS", user_id=test_user.id)
    hidden = Company(name="HiddenCo", industry="Healthcare", user_id=other_user.id)
    db.add_all([visible, hidden])
    db.flush()

    listing = client.get("/api/v1/companies/").json()
    names = {item["name"] for item in listing["items"]}

    assert names == {"VisibleCo"}
    assert client.get(f"/api/v1/companies/{visible.id}").status_code == 200
    assert client.get(f"/api/v1/companies/{hidden.id}").status_code == 404
    assert (
        client.patch(
            f"/api/v1/companies/{hidden.id}",
            json={"notes": "should not leak existence"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/companies/{hidden.id}").status_code == 404


def test_company_names_are_unique_per_user(
    client: TestClient, db: Session
) -> None:
    other_user = _create_user(db, "other-user")
    db.add(Company(name="Shared Name", user_id=other_user.id))
    db.flush()

    response = client.post("/api/v1/companies/", json={"name": "Shared Name"})

    assert response.status_code == 201
    assert response.json()["name"] == "Shared Name"


def test_application_access_and_foreign_keys_are_scoped(
    client: TestClient, db: Session, test_user: User
) -> None:
    other_user = _create_user(db, "other-user")
    visible_company = Company(name="Visible App Co", user_id=test_user.id)
    hidden_company = Company(name="Hidden App Co", user_id=other_user.id)
    db.add_all([visible_company, hidden_company])
    db.flush()
    hidden_application = JobApplication(
        company_id=hidden_company.id,
        job_title="Hidden Engineer",
        status=ApplicationStatus.APPLIED.value,
        date_applied=date.today(),
        user_id=other_user.id,
    )
    db.add(hidden_application)
    db.flush()

    listing = client.get("/api/v1/applications/").json()

    assert listing["total"] == 0
    assert client.get(f"/api/v1/applications/{hidden_application.id}").status_code == 404
    assert (
        client.patch(
            f"/api/v1/applications/{hidden_application.id}",
            json={"notes": "should not leak existence"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/applications/{hidden_application.id}").status_code == 404

    cross_user_create = client.post(
        "/api/v1/applications/",
        json={
            "company_id": str(hidden_company.id),
            "job_title": "Cross-user Engineer",
        },
    )
    own_create = client.post(
        "/api/v1/applications/",
        json={
            "company_id": str(visible_company.id),
            "job_title": "Visible Engineer",
        },
    )

    assert cross_user_create.status_code == 404
    assert own_create.status_code == 201
