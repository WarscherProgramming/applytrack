from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

_SCHEDULED_AT = "2024-06-15T14:00:00Z"
_EARLIER = "2024-01-01T09:00:00Z"
_LATER = "2024-12-31T17:00:00Z"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def company(client: TestClient) -> dict:
    resp = client.post("/api/v1/companies/", json={"name": "Interview Corp"})
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def application(client: TestClient, company: dict) -> dict:
    resp = client.post(
        "/api/v1/applications/",
        json={"company_id": company["id"], "job_title": "Software Engineer"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def other_application(client: TestClient, company: dict) -> dict:
    resp = client.post(
        "/api/v1/applications/",
        json={"company_id": company["id"], "job_title": "Product Manager"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def recruiter(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/recruiters/",
        json={"first_name": "Jane", "last_name": "Recruiter"},
    )
    assert resp.status_code == 201
    return resp.json()


def _create_interview(
    client: TestClient, application_id: str, **kwargs
) -> dict:
    payload = {
        "application_id": application_id,
        "scheduled_at": _SCHEDULED_AT,
        **kwargs,
    }
    resp = client.post("/api/v1/interviews/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /api/v1/interviews/
# ---------------------------------------------------------------------------


class TestCreateInterview:
    def test_returns_201_with_all_fields(
        self, client: TestClient, application: dict, recruiter: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={
                "application_id": application["id"],
                "recruiter_id": recruiter["id"],
                "interview_type": "technical",
                "scheduled_at": _SCHEDULED_AT,
                "duration_minutes": 60,
                "location": "HQ Floor 3",
                "meeting_link": "https://meet.example.com/abc",
                "status": "scheduled",
                "notes": "Bring portfolio.",
                "feedback": None,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["application_id"] == application["id"]
        assert body["recruiter_id"] == recruiter["id"]
        assert body["interview_type"] == "technical"
        assert body["scheduled_at"] is not None
        assert body["duration_minutes"] == 60
        assert body["location"] == "HQ Floor 3"
        assert body["meeting_link"] == "https://meet.example.com/abc"
        assert body["status"] == "scheduled"
        assert body["notes"] == "Bring portfolio."
        assert body["feedback"] is None
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_returns_201_with_required_fields_only(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={
                "application_id": application["id"],
                "scheduled_at": _SCHEDULED_AT,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["application_id"] == application["id"]
        assert body["recruiter_id"] is None
        assert body["interview_type"] is None
        assert body["duration_minutes"] == 30
        assert body["status"] == "scheduled"

    def test_status_defaults_to_scheduled(
        self, client: TestClient, application: dict
    ) -> None:
        body = _create_interview(client, application["id"])
        assert body["status"] == "scheduled"

    def test_duration_defaults_to_30(
        self, client: TestClient, application: dict
    ) -> None:
        body = _create_interview(client, application["id"])
        assert body["duration_minutes"] == 30

    def test_returns_404_when_application_does_not_exist(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={"application_id": str(uuid4()), "scheduled_at": _SCHEDULED_AT},
        )
        assert resp.status_code == 404

    def test_returns_404_when_recruiter_does_not_exist(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={
                "application_id": application["id"],
                "recruiter_id": str(uuid4()),
                "scheduled_at": _SCHEDULED_AT,
            },
        )
        assert resp.status_code == 404

    def test_returns_422_when_application_id_is_missing(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/", json={"scheduled_at": _SCHEDULED_AT}
        )
        assert resp.status_code == 422

    def test_returns_422_when_scheduled_at_is_missing(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/", json={"application_id": application["id"]}
        )
        assert resp.status_code == 422

    def test_returns_422_when_duration_is_below_minimum(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={
                "application_id": application["id"],
                "scheduled_at": _SCHEDULED_AT,
                "duration_minutes": 14,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_duration_exceeds_maximum(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={
                "application_id": application["id"],
                "scheduled_at": _SCHEDULED_AT,
                "duration_minutes": 481,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_interview_type_is_invalid(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={
                "application_id": application["id"],
                "scheduled_at": _SCHEDULED_AT,
                "interview_type": "surprise",
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_status_is_invalid(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/interviews/",
            json={
                "application_id": application["id"],
                "scheduled_at": _SCHEDULED_AT,
                "status": "ghost",
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/interviews/{id}
# ---------------------------------------------------------------------------


class TestGetInterview:
    def test_returns_interview_by_id(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(
            client, application["id"], interview_type="technical"
        )
        resp = client.get(f"/api/v1/interviews/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["interview_type"] == "technical"

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        assert client.get(f"/api/v1/interviews/{uuid4()}").status_code == 404

    def test_returns_422_for_invalid_uuid(self, client: TestClient) -> None:
        assert client.get("/api/v1/interviews/not-a-uuid").status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/interviews/
# ---------------------------------------------------------------------------


class TestListInterviews:
    def test_returns_empty_list_when_no_interviews_exist(
        self, client: TestClient
    ) -> None:
        resp = client.get("/api/v1/interviews/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_returns_all_interviews_with_correct_total(
        self, client: TestClient, application: dict
    ) -> None:
        _create_interview(client, application["id"])
        _create_interview(client, application["id"])
        body = client.get("/api/v1/interviews/").json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_filter_by_application_id(
        self, client: TestClient, application: dict, other_application: dict
    ) -> None:
        _create_interview(client, application["id"])
        _create_interview(client, application["id"])
        _create_interview(client, other_application["id"])
        body = client.get(
            f"/api/v1/interviews/?application_id={application['id']}"
        ).json()
        assert body["total"] == 2
        assert all(
            item["application_id"] == application["id"] for item in body["items"]
        )

    def test_filter_by_recruiter_id(
        self, client: TestClient, application: dict, recruiter: dict
    ) -> None:
        _create_interview(client, application["id"], recruiter_id=recruiter["id"])
        _create_interview(client, application["id"])  # no recruiter
        body = client.get(
            f"/api/v1/interviews/?recruiter_id={recruiter['id']}"
        ).json()
        assert body["total"] == 1
        assert body["items"][0]["recruiter_id"] == recruiter["id"]

    def test_filter_by_status(
        self, client: TestClient, application: dict
    ) -> None:
        _create_interview(client, application["id"], status="completed")
        _create_interview(client, application["id"], status="completed")
        _create_interview(client, application["id"], status="cancelled")
        body = client.get("/api/v1/interviews/?status=completed").json()
        assert body["total"] == 2
        assert all(item["status"] == "completed" for item in body["items"])

    def test_filter_by_interview_type(
        self, client: TestClient, application: dict
    ) -> None:
        _create_interview(client, application["id"], interview_type="technical")
        _create_interview(client, application["id"], interview_type="technical")
        _create_interview(client, application["id"], interview_type="behavioral")
        body = client.get("/api/v1/interviews/?interview_type=technical").json()
        assert body["total"] == 2
        assert all(
            item["interview_type"] == "technical" for item in body["items"]
        )

    def test_pagination_returns_correct_page_size(
        self, client: TestClient, application: dict
    ) -> None:
        for _ in range(5):
            _create_interview(client, application["id"])
        body = client.get("/api/v1/interviews/?skip=0&limit=2").json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 2

    def test_pagination_pages_are_non_overlapping(
        self, client: TestClient, application: dict
    ) -> None:
        for _ in range(5):
            _create_interview(client, application["id"])
        first = {
            r["id"]
            for r in client.get("/api/v1/interviews/?skip=0&limit=3").json()["items"]
        }
        second = {
            r["id"]
            for r in client.get("/api/v1/interviews/?skip=3&limit=3").json()["items"]
        }
        assert first.isdisjoint(second)

    def test_default_sort_is_scheduled_at_ascending(
        self, client: TestClient, application: dict
    ) -> None:
        # scheduled_at is client-controlled, so we can use distinct explicit
        # values to verify sort order — no "same timestamp in transaction" issue.
        earlier = _create_interview(
            client, application["id"], scheduled_at=_EARLIER
        )
        later = _create_interview(
            client, application["id"], scheduled_at=_LATER
        )
        items = client.get("/api/v1/interviews/").json()["items"]
        ids = [item["id"] for item in items]
        assert ids.index(earlier["id"]) < ids.index(later["id"])

    def test_returns_422_when_limit_exceeds_maximum(
        self, client: TestClient
    ) -> None:
        assert client.get("/api/v1/interviews/?limit=101").status_code == 422

    def test_returns_422_when_skip_is_negative(self, client: TestClient) -> None:
        assert client.get("/api/v1/interviews/?skip=-1").status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/interviews/{id}
# ---------------------------------------------------------------------------


class TestUpdateInterview:
    def test_updates_single_field_leaves_others_unchanged(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(
            client, application["id"], interview_type="technical", duration_minutes=45
        )
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}",
            json={"status": "completed"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["interview_type"] == "technical"
        assert body["duration_minutes"] == 45

    def test_updates_scheduled_at(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}",
            json={"scheduled_at": _LATER},
        )
        assert resp.status_code == 200
        assert resp.json()["scheduled_at"] is not None

    def test_clears_nullable_field_by_sending_null(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(
            client, application["id"], location="HQ Floor 3"
        )
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}", json={"location": None}
        )
        assert resp.status_code == 200
        assert resp.json()["location"] is None

    def test_assigns_recruiter(
        self, client: TestClient, application: dict, recruiter: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}",
            json={"recruiter_id": recruiter["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["recruiter_id"] == recruiter["id"]

    def test_detaches_recruiter_by_sending_null(
        self, client: TestClient, application: dict, recruiter: dict
    ) -> None:
        created = _create_interview(
            client, application["id"], recruiter_id=recruiter["id"]
        )
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}", json={"recruiter_id": None}
        )
        assert resp.status_code == 200
        assert resp.json()["recruiter_id"] is None

    def test_reassigns_to_another_application(
        self, client: TestClient, application: dict, other_application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}",
            json={"application_id": other_application["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["application_id"] == other_application["id"]

    def test_returns_404_when_new_application_does_not_exist(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}",
            json={"application_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_returns_404_when_new_recruiter_does_not_exist(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}",
            json={"recruiter_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_returns_422_when_duration_is_below_minimum(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}", json={"duration_minutes": 5}
        )
        assert resp.status_code == 422

    def test_returns_422_when_duration_exceeds_maximum(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        resp = client.patch(
            f"/api/v1/interviews/{created['id']}", json={"duration_minutes": 999}
        )
        assert resp.status_code == 422

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        resp = client.patch(
            f"/api/v1/interviews/{uuid4()}", json={"status": "completed"}
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/interviews/{id}
# ---------------------------------------------------------------------------


class TestDeleteInterview:
    def test_returns_204_on_success(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        assert client.delete(f"/api/v1/interviews/{created['id']}").status_code == 204

    def test_interview_is_not_retrievable_after_deletion(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_interview(client, application["id"])
        client.delete(f"/api/v1/interviews/{created['id']}")
        assert client.get(f"/api/v1/interviews/{created['id']}").status_code == 404

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        assert client.delete(f"/api/v1/interviews/{uuid4()}").status_code == 404

    def test_deleting_application_cascades_to_interviews(
        self, client: TestClient, application: dict
    ) -> None:
        # Confirms the CASCADE FK is wired correctly end-to-end.
        interview = _create_interview(client, application["id"])
        client.delete(f"/api/v1/applications/{application['id']}")
        assert (
            client.get(f"/api/v1/interviews/{interview['id']}").status_code == 404
        )
