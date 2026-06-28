from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.features.users.model import User


def _register(client: TestClient, email: str = "person@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass1",
            "full_name": "Job Seeker",
        },
    )
    assert response.status_code == 201
    return response.json()


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_login_me_and_account_update(client: TestClient) -> None:
    registered = _register(client)
    assert registered["token_type"] == "bearer"
    assert registered["access_token"]
    assert registered["refresh_token"]
    assert registered["user"]["email"] == "person@example.com"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "StrongPass1"},
    )
    assert login.status_code == 200

    me = client.get(
        "/api/v1/auth/me",
        headers=_auth_header(login.json()["access_token"]),
    )
    assert me.status_code == 200
    assert me.json()["full_name"] == "Job Seeker"

    update = client.patch(
        "/api/v1/users/me",
        json={"full_name": "Zack Jobseeker", "email": "zack@example.com"},
        headers=_auth_header(login.json()["access_token"]),
    )
    assert update.status_code == 200
    assert update.json()["full_name"] == "Zack Jobseeker"
    assert update.json()["email"] == "zack@example.com"


def test_registration_validates_password_and_email_uniqueness(
    client: TestClient, db: Session
) -> None:
    weak = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "password", "full_name": "Weak"},
    )
    assert weak.status_code == 422

    first = _register(client, "unique@example.com")
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "unique@example.com",
            "password": "StrongPass1",
            "full_name": "Duplicate",
        },
    )
    user = db.query(User).filter(User.email == "unique@example.com").one()

    assert first["user"]["id"] == str(user.id)
    assert duplicate.status_code == 409
    assert user.hashed_password != "StrongPass1"


def test_refresh_rotates_and_logout_revokes_refresh_token(client: TestClient) -> None:
    registered = _register(client, "refresh@example.com")
    old_refresh = registered["refresh_token"]

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]
    assert refresh.json()["refresh_token"] != old_refresh

    reused = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reused.status_code == 401

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh.json()["refresh_token"]},
        headers=_auth_header(refresh.json()["access_token"]),
    )
    assert logout.status_code == 200
    assert logout.json()["logged_out"] is True

    after_logout = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh.json()["refresh_token"]},
    )
    assert after_logout.status_code == 401


def test_protected_current_user_requires_bearer_token(
    anonymous_client: TestClient,
) -> None:
    unauthenticated = anonymous_client.get("/api/v1/auth/me")

    assert unauthenticated.status_code == 401
