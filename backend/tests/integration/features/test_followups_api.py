from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Dates are computed relative to "today" (UTC) so the overdue / today /
# upcoming reminder tests stay stable regardless of when they run.
_TODAY = datetime.now(timezone.utc).date()
_YESTERDAY = (_TODAY - timedelta(days=1)).isoformat()
_TODAY_ISO = _TODAY.isoformat()
_IN_THREE_DAYS = (_TODAY + timedelta(days=3)).isoformat()
_NEXT_MONTH = (_TODAY + timedelta(days=30)).isoformat()
_DUE_DEFAULT = (_TODAY + timedelta(days=7)).isoformat()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def company(client: TestClient) -> dict:
    resp = client.post("/api/v1/companies/", json={"name": "FollowUp Corp"})
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


@pytest.fixture
def interview(client: TestClient, application: dict) -> dict:
    resp = client.post(
        "/api/v1/interviews/",
        json={
            "application_id": application["id"],
            "scheduled_at": "2024-06-15T14:00:00Z",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _create_followup(client: TestClient, application_id: str, **kwargs) -> dict:
    payload = {
        "application_id": application_id,
        "title": "Send thank-you note",
        "followup_type": "email",
        "due_date": _DUE_DEFAULT,
        **kwargs,
    }
    resp = client.post("/api/v1/followups/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /api/v1/followups/
# ---------------------------------------------------------------------------


class TestCreateFollowUp:
    def test_returns_201_with_all_fields(
        self,
        client: TestClient,
        application: dict,
        recruiter: dict,
        interview: dict,
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "recruiter_id": recruiter["id"],
                "interview_id": interview["id"],
                "title": "Follow up after onsite",
                "description": "Email the hiring manager to reiterate interest.",
                "followup_type": "interview_followup",
                "status": "pending",
                "priority": "high",
                "due_date": _IN_THREE_DAYS,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["application_id"] == application["id"]
        assert body["recruiter_id"] == recruiter["id"]
        assert body["interview_id"] == interview["id"]
        assert body["title"] == "Follow up after onsite"
        assert body["description"] == "Email the hiring manager to reiterate interest."
        assert body["followup_type"] == "interview_followup"
        assert body["status"] == "pending"
        assert body["priority"] == "high"
        assert body["due_date"] == _IN_THREE_DAYS
        assert body["completed_at"] is None
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_defaults_status_pending_and_priority_medium(
        self, client: TestClient, application: dict
    ) -> None:
        body = _create_followup(client, application["id"])
        assert body["status"] == "pending"
        assert body["priority"] == "medium"

    def test_optional_fks_are_null_when_omitted(
        self, client: TestClient, application: dict
    ) -> None:
        body = _create_followup(client, application["id"])
        assert body["recruiter_id"] is None
        assert body["interview_id"] is None
        assert body["description"] is None
        assert body["completed_at"] is None

    def test_creating_completed_auto_populates_completed_at(
        self, client: TestClient, application: dict
    ) -> None:
        body = _create_followup(client, application["id"], status="completed")
        assert body["status"] == "completed"
        assert body["completed_at"] is not None

    def test_allows_past_due_date(
        self, client: TestClient, application: dict
    ) -> None:
        body = _create_followup(client, application["id"], due_date=_YESTERDAY)
        assert body["due_date"] == _YESTERDAY

    def test_returns_404_when_application_does_not_exist(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": str(uuid4()),
                "title": "Orphan",
                "followup_type": "email",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 404

    def test_returns_404_when_recruiter_does_not_exist(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "recruiter_id": str(uuid4()),
                "title": "Bad recruiter",
                "followup_type": "email",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 404

    def test_returns_404_when_interview_does_not_exist(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "interview_id": str(uuid4()),
                "title": "Bad interview",
                "followup_type": "email",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 404

    def test_returns_422_when_application_id_missing(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={"title": "X", "followup_type": "email", "due_date": _DUE_DEFAULT},
        )
        assert resp.status_code == 422

    def test_returns_422_when_title_missing(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "followup_type": "email",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_title_is_empty(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "title": "",
                "followup_type": "email",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_title_exceeds_max_length(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "title": "x" * 256,
                "followup_type": "email",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_description_exceeds_max_length(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "title": "X",
                "description": "x" * 5001,
                "followup_type": "email",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_followup_type_missing(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "title": "X",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_when_due_date_missing(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "title": "X",
                "followup_type": "email",
            },
        )
        assert resp.status_code == 422

    def test_returns_422_for_invalid_followup_type(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "title": "X",
                "followup_type": "carrier_pigeon",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 422

    def test_returns_422_for_invalid_priority(
        self, client: TestClient, application: dict
    ) -> None:
        resp = client.post(
            "/api/v1/followups/",
            json={
                "application_id": application["id"],
                "title": "X",
                "followup_type": "email",
                "priority": "critical",
                "due_date": _DUE_DEFAULT,
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/followups/{id}
# ---------------------------------------------------------------------------


class TestGetFollowUp:
    def test_returns_followup_by_id(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"], title="Specific note")
        resp = client.get(f"/api/v1/followups/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Specific note"

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        assert client.get(f"/api/v1/followups/{uuid4()}").status_code == 404

    def test_returns_422_for_invalid_uuid(self, client: TestClient) -> None:
        assert client.get("/api/v1/followups/not-a-uuid").status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/followups/  (list, filters, pagination, sorting)
# ---------------------------------------------------------------------------


class TestListFollowUps:
    def test_returns_empty_list_when_none_exist(self, client: TestClient) -> None:
        resp = client.get("/api/v1/followups/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_returns_all_with_correct_total(
        self, client: TestClient, application: dict
    ) -> None:
        _create_followup(client, application["id"], title="A")
        _create_followup(client, application["id"], title="B")
        body = client.get("/api/v1/followups/").json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_filter_by_application_id(
        self, client: TestClient, application: dict, other_application: dict
    ) -> None:
        _create_followup(client, application["id"], title="A1")
        _create_followup(client, application["id"], title="A2")
        _create_followup(client, other_application["id"], title="B1")
        body = client.get(
            f"/api/v1/followups/?application_id={application['id']}"
        ).json()
        assert body["total"] == 2
        assert all(i["application_id"] == application["id"] for i in body["items"])

    def test_filter_by_recruiter_id(
        self, client: TestClient, application: dict, recruiter: dict
    ) -> None:
        _create_followup(client, application["id"], recruiter_id=recruiter["id"])
        _create_followup(client, application["id"])
        body = client.get(
            f"/api/v1/followups/?recruiter_id={recruiter['id']}"
        ).json()
        assert body["total"] == 1
        assert body["items"][0]["recruiter_id"] == recruiter["id"]

    def test_filter_by_interview_id(
        self, client: TestClient, application: dict, interview: dict
    ) -> None:
        _create_followup(client, application["id"], interview_id=interview["id"])
        _create_followup(client, application["id"])
        body = client.get(
            f"/api/v1/followups/?interview_id={interview['id']}"
        ).json()
        assert body["total"] == 1
        assert body["items"][0]["interview_id"] == interview["id"]

    def test_filter_by_status(
        self, client: TestClient, application: dict
    ) -> None:
        _create_followup(client, application["id"], status="completed")
        _create_followup(client, application["id"], status="pending")
        _create_followup(client, application["id"], status="pending")
        body = client.get("/api/v1/followups/?status=pending").json()
        assert body["total"] == 2
        assert all(i["status"] == "pending" for i in body["items"])

    def test_filter_by_priority(
        self, client: TestClient, application: dict
    ) -> None:
        _create_followup(client, application["id"], priority="urgent")
        _create_followup(client, application["id"], priority="low")
        body = client.get("/api/v1/followups/?priority=urgent").json()
        assert body["total"] == 1
        assert body["items"][0]["priority"] == "urgent"

    def test_filter_by_followup_type(
        self, client: TestClient, application: dict
    ) -> None:
        _create_followup(client, application["id"], followup_type="linkedin")
        _create_followup(client, application["id"], followup_type="email")
        body = client.get("/api/v1/followups/?followup_type=linkedin").json()
        assert body["total"] == 1
        assert body["items"][0]["followup_type"] == "linkedin"

    def test_pagination_returns_correct_page_size(
        self, client: TestClient, application: dict
    ) -> None:
        for i in range(5):
            _create_followup(client, application["id"], title=f"Note {i:02d}")
        body = client.get("/api/v1/followups/?skip=0&limit=2").json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 2

    def test_pagination_pages_are_non_overlapping(
        self, client: TestClient, application: dict
    ) -> None:
        for i in range(5):
            _create_followup(client, application["id"], title=f"Note {i:02d}")
        first = {
            i["id"]
            for i in client.get("/api/v1/followups/?skip=0&limit=3").json()["items"]
        }
        second = {
            i["id"]
            for i in client.get("/api/v1/followups/?skip=3&limit=3").json()["items"]
        }
        assert first.isdisjoint(second)

    def test_default_sort_is_due_date_ascending(
        self, client: TestClient, application: dict
    ) -> None:
        later = _create_followup(
            client, application["id"], title="Later", due_date=_NEXT_MONTH
        )
        earlier = _create_followup(
            client, application["id"], title="Earlier", due_date=_TODAY_ISO
        )
        items = client.get("/api/v1/followups/").json()["items"]
        ids = [i["id"] for i in items]
        assert ids.index(earlier["id"]) < ids.index(later["id"])

    def test_returns_422_when_limit_exceeds_maximum(self, client: TestClient) -> None:
        assert client.get("/api/v1/followups/?limit=101").status_code == 422

    def test_returns_422_when_skip_is_negative(self, client: TestClient) -> None:
        assert client.get("/api/v1/followups/?skip=-1").status_code == 422


# ---------------------------------------------------------------------------
# Reminder endpoints: /overdue, /today, /upcoming
# ---------------------------------------------------------------------------


class TestReminderEndpoints:
    def test_overdue_returns_past_due_pending_items(
        self, client: TestClient, application: dict
    ) -> None:
        overdue = _create_followup(
            client, application["id"], title="Late", due_date=_YESTERDAY
        )
        _create_followup(
            client, application["id"], title="Future", due_date=_NEXT_MONTH
        )
        body = client.get("/api/v1/followups/overdue").json()
        ids = {i["id"] for i in body["items"]}
        assert overdue["id"] in ids
        assert all(i["status"] == "pending" for i in body["items"])
        assert body["total"] == 1

    def test_overdue_excludes_completed_items(
        self, client: TestClient, application: dict
    ) -> None:
        # Past due but already completed — should NOT be an overdue reminder.
        _create_followup(
            client,
            application["id"],
            title="Done late",
            due_date=_YESTERDAY,
            status="completed",
        )
        body = client.get("/api/v1/followups/overdue").json()
        assert body["total"] == 0

    def test_completing_an_overdue_item_removes_it_from_overdue(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(
            client, application["id"], title="Late", due_date=_YESTERDAY
        )
        assert client.get("/api/v1/followups/overdue").json()["total"] == 1
        client.patch(
            f"/api/v1/followups/{created['id']}", json={"status": "completed"}
        )
        assert client.get("/api/v1/followups/overdue").json()["total"] == 0

    def test_today_returns_items_due_today(
        self, client: TestClient, application: dict
    ) -> None:
        today_item = _create_followup(
            client, application["id"], title="Today", due_date=_TODAY_ISO
        )
        _create_followup(
            client, application["id"], title="Yesterday", due_date=_YESTERDAY
        )
        _create_followup(
            client, application["id"], title="Future", due_date=_NEXT_MONTH
        )
        body = client.get("/api/v1/followups/today").json()
        ids = {i["id"] for i in body["items"]}
        assert today_item["id"] in ids
        assert body["total"] == 1

    def test_upcoming_returns_items_within_seven_days(
        self, client: TestClient, application: dict
    ) -> None:
        soon = _create_followup(
            client, application["id"], title="Soon", due_date=_IN_THREE_DAYS
        )
        _create_followup(
            client, application["id"], title="FarOff", due_date=_NEXT_MONTH
        )
        body = client.get("/api/v1/followups/upcoming").json()
        ids = {i["id"] for i in body["items"]}
        assert soon["id"] in ids
        assert all(i["id"] != _NEXT_MONTH for i in body["items"])
        assert body["total"] == 1

    def test_upcoming_excludes_overdue_items(
        self, client: TestClient, application: dict
    ) -> None:
        _create_followup(
            client, application["id"], title="Late", due_date=_YESTERDAY
        )
        body = client.get("/api/v1/followups/upcoming").json()
        assert body["total"] == 0

    def test_reminder_endpoints_support_pagination(
        self, client: TestClient, application: dict
    ) -> None:
        for i in range(3):
            _create_followup(
                client, application["id"], title=f"Late {i}", due_date=_YESTERDAY
            )
        body = client.get("/api/v1/followups/overdue?skip=0&limit=2").json()
        assert len(body["items"]) == 2
        assert body["total"] == 3


# ---------------------------------------------------------------------------
# PATCH /api/v1/followups/{id}
# ---------------------------------------------------------------------------


class TestUpdateFollowUp:
    def test_updates_single_field_leaves_others_unchanged(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(
            client, application["id"], title="Original", priority="low"
        )
        resp = client.patch(
            f"/api/v1/followups/{created['id']}", json={"priority": "high"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["priority"] == "high"
        assert body["title"] == "Original"

    def test_completing_auto_sets_completed_at(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"])
        assert created["completed_at"] is None
        resp = client.patch(
            f"/api/v1/followups/{created['id']}", json={"status": "completed"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["completed_at"] is not None

    def test_reopening_clears_completed_at(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"], status="completed")
        assert created["completed_at"] is not None
        resp = client.patch(
            f"/api/v1/followups/{created['id']}", json={"status": "pending"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending"
        assert body["completed_at"] is None

    def test_explicit_completed_at_is_respected(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"])
        stamp = "2024-05-01T08:30:00Z"
        resp = client.patch(
            f"/api/v1/followups/{created['id']}",
            json={"status": "completed", "completed_at": stamp},
        )
        assert resp.status_code == 200
        # The explicit value wins over the auto-stamp.
        assert resp.json()["completed_at"].startswith("2024-05-01T08:30:00")

    def test_clears_nullable_field_with_null(
        self, client: TestClient, application: dict, recruiter: dict
    ) -> None:
        created = _create_followup(
            client, application["id"], recruiter_id=recruiter["id"]
        )
        resp = client.patch(
            f"/api/v1/followups/{created['id']}", json={"recruiter_id": None}
        )
        assert resp.status_code == 200
        assert resp.json()["recruiter_id"] is None

    def test_reassigns_to_another_application(
        self, client: TestClient, application: dict, other_application: dict
    ) -> None:
        created = _create_followup(client, application["id"])
        resp = client.patch(
            f"/api/v1/followups/{created['id']}",
            json={"application_id": other_application["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["application_id"] == other_application["id"]

    def test_returns_404_when_new_application_missing(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"])
        resp = client.patch(
            f"/api/v1/followups/{created['id']}",
            json={"application_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_returns_404_when_new_recruiter_missing(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"])
        resp = client.patch(
            f"/api/v1/followups/{created['id']}",
            json={"recruiter_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        resp = client.patch(
            f"/api/v1/followups/{uuid4()}", json={"title": "New"}
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/followups/{id}  and  cascade / set-null behaviour
# ---------------------------------------------------------------------------


class TestDeleteFollowUp:
    def test_returns_204_on_success(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"])
        assert client.delete(f"/api/v1/followups/{created['id']}").status_code == 204

    def test_followup_not_retrievable_after_deletion(
        self, client: TestClient, application: dict
    ) -> None:
        created = _create_followup(client, application["id"])
        client.delete(f"/api/v1/followups/{created['id']}")
        assert client.get(f"/api/v1/followups/{created['id']}").status_code == 404

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        assert client.delete(f"/api/v1/followups/{uuid4()}").status_code == 404

    def test_deleting_recruiter_sets_followup_recruiter_null(
        self, client: TestClient, application: dict, recruiter: dict
    ) -> None:
        created = _create_followup(
            client, application["id"], recruiter_id=recruiter["id"]
        )
        assert client.delete(f"/api/v1/recruiters/{recruiter['id']}").status_code == 204
        body = client.get(f"/api/v1/followups/{created['id']}").json()
        assert body["recruiter_id"] is None

    def test_deleting_interview_sets_followup_interview_null(
        self, client: TestClient, application: dict, interview: dict
    ) -> None:
        created = _create_followup(
            client, application["id"], interview_id=interview["id"]
        )
        assert client.delete(f"/api/v1/interviews/{interview['id']}").status_code == 204
        body = client.get(f"/api/v1/followups/{created['id']}").json()
        assert body["interview_id"] is None
