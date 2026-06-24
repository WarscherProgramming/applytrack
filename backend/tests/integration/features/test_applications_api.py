from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def company(client: TestClient) -> dict:
    resp = client.post("/api/v1/companies/", json={"name": "Acme Corp"})
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def other_company(client: TestClient) -> dict:
    resp = client.post("/api/v1/companies/", json={"name": "Other Corp"})
    assert resp.status_code == 201
    return resp.json()


def _create_application(
    client: TestClient, company_id: str, **kwargs
) -> dict:
    payload = {"company_id": company_id, "job_title": "Software Engineer", **kwargs}
    resp = client.post("/api/v1/applications/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /api/v1/applications/
# ---------------------------------------------------------------------------


class TestCreateApplication:
    def test_returns_201_with_all_fields(self, client: TestClient, company: dict) -> None:
        resp = client.post(
            "/api/v1/applications/",
            json={
                "company_id": company["id"],
                "job_title": "Backend Engineer",
                "job_link": "https://acme.com/jobs/123",
                "location": "Remote",
                "salary_range": "$120k–$150k",
                "status": "applied",
                "date_applied": "2024-06-01",
                "source": "LinkedIn",
                "notes": "Referred by Jane.",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["company_id"] == company["id"]
        assert body["job_title"] == "Backend Engineer"
        assert body["job_link"] == "https://acme.com/jobs/123"
        assert body["location"] == "Remote"
        assert body["salary_range"] == "$120k–$150k"
        assert body["status"] == "applied"
        assert body["date_applied"] == "2024-06-01"
        assert body["source"] == "LinkedIn"
        assert body["notes"] == "Referred by Jane."
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_status_defaults_to_draft_when_omitted(
        self, client: TestClient, company: dict
    ) -> None:
        resp = client.post(
            "/api/v1/applications/",
            json={"company_id": company["id"], "job_title": "Backend Engineer"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "draft"

    def test_optional_fields_are_null_when_omitted(
        self, client: TestClient, company: dict
    ) -> None:
        body = _create_application(client, company["id"])
        assert body["job_link"] is None
        assert body["location"] is None
        assert body["salary_range"] is None
        assert body["date_applied"] is None
        assert body["source"] is None
        assert body["notes"] is None

    def test_returns_404_when_company_does_not_exist(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/applications/",
            json={"company_id": str(uuid4()), "job_title": "Engineer"},
        )
        assert resp.status_code == 404

    def test_returns_422_when_company_id_is_missing(self, client: TestClient) -> None:
        resp = client.post("/api/v1/applications/", json={"job_title": "Engineer"})
        assert resp.status_code == 422

    def test_returns_422_when_job_title_is_missing(
        self, client: TestClient, company: dict
    ) -> None:
        resp = client.post(
            "/api/v1/applications/", json={"company_id": company["id"]}
        )
        assert resp.status_code == 422

    def test_returns_422_when_job_title_is_empty(
        self, client: TestClient, company: dict
    ) -> None:
        resp = client.post(
            "/api/v1/applications/",
            json={"company_id": company["id"], "job_title": ""},
        )
        assert resp.status_code == 422

    def test_returns_422_when_job_title_is_only_whitespace(
        self, client: TestClient, company: dict
    ) -> None:
        resp = client.post(
            "/api/v1/applications/",
            json={"company_id": company["id"], "job_title": "   "},
        )
        assert resp.status_code == 422

    def test_returns_422_when_status_is_invalid(
        self, client: TestClient, company: dict
    ) -> None:
        resp = client.post(
            "/api/v1/applications/",
            json={"company_id": company["id"], "job_title": "Engineer", "status": "promoted"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/applications/{id}
# ---------------------------------------------------------------------------


class TestGetApplication:
    def test_returns_application_by_id(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_application(client, company["id"], job_title="ML Engineer")
        resp = client.get(f"/api/v1/applications/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["job_title"] == "ML Engineer"

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        resp = client.get(f"/api/v1/applications/{uuid4()}")
        assert resp.status_code == 404

    def test_returns_422_for_invalid_uuid(self, client: TestClient) -> None:
        resp = client.get("/api/v1/applications/not-a-uuid")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/applications/
# ---------------------------------------------------------------------------


class TestListApplications:
    def test_returns_empty_list_when_no_applications_exist(
        self, client: TestClient
    ) -> None:
        resp = client.get("/api/v1/applications/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_returns_all_applications_with_correct_total(
        self, client: TestClient, company: dict
    ) -> None:
        _create_application(client, company["id"], job_title="Engineer A")
        _create_application(client, company["id"], job_title="Engineer B")
        body = client.get("/api/v1/applications/").json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_search_filters_by_job_title_case_insensitively(
        self, client: TestClient, company: dict
    ) -> None:
        _create_application(client, company["id"], job_title="Backend Engineer")
        _create_application(client, company["id"], job_title="Frontend Engineer")
        _create_application(client, company["id"], job_title="Product Manager")
        body = client.get("/api/v1/applications/?query=engineer").json()
        assert body["total"] == 2
        titles = {item["job_title"] for item in body["items"]}
        assert titles == {"Backend Engineer", "Frontend Engineer"}

    def test_search_returns_partial_match(
        self, client: TestClient, company: dict
    ) -> None:
        _create_application(client, company["id"], job_title="Senior Backend Engineer")
        _create_application(client, company["id"], job_title="Backend Engineer")
        _create_application(client, company["id"], job_title="Designer")
        body = client.get("/api/v1/applications/?query=backend").json()
        assert body["total"] == 2

    def test_filter_by_status_returns_matching_applications(
        self, client: TestClient, company: dict
    ) -> None:
        _create_application(client, company["id"], status="applied")
        _create_application(client, company["id"], status="applied")
        _create_application(client, company["id"], status="interview")
        body = client.get("/api/v1/applications/?status=applied").json()
        assert body["total"] == 2
        assert all(item["status"] == "applied" for item in body["items"])

    def test_filter_by_company_id_returns_only_that_companys_applications(
        self, client: TestClient, company: dict, other_company: dict
    ) -> None:
        _create_application(client, company["id"], job_title="Engineer at Acme")
        _create_application(client, company["id"], job_title="PM at Acme")
        _create_application(client, other_company["id"], job_title="Engineer at Other")
        body = client.get(f"/api/v1/applications/?company_id={company['id']}").json()
        assert body["total"] == 2
        assert all(item["company_id"] == company["id"] for item in body["items"])

    def test_combining_query_and_status_filters(
        self, client: TestClient, company: dict
    ) -> None:
        _create_application(client, company["id"], job_title="Backend Engineer", status="applied")
        _create_application(client, company["id"], job_title="Backend Engineer", status="interview")
        _create_application(client, company["id"], job_title="Frontend Engineer", status="applied")
        body = client.get("/api/v1/applications/?query=backend&status=applied").json()
        assert body["total"] == 1
        assert body["items"][0]["job_title"] == "Backend Engineer"
        assert body["items"][0]["status"] == "applied"

    def test_pagination_returns_correct_page_size(
        self, client: TestClient, company: dict
    ) -> None:
        for i in range(5):
            _create_application(client, company["id"], job_title=f"Role {i:02d}")
        body = client.get("/api/v1/applications/?skip=0&limit=2").json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 2

    def test_pagination_pages_are_non_overlapping(
        self, client: TestClient, company: dict
    ) -> None:
        for i in range(5):
            _create_application(client, company["id"], job_title=f"Role {i:02d}")
        first = {item["id"] for item in client.get("/api/v1/applications/?skip=0&limit=3").json()["items"]}
        second = {item["id"] for item in client.get("/api/v1/applications/?skip=3&limit=3").json()["items"]}
        assert first.isdisjoint(second)

    def test_default_sort_places_applications_with_dates_before_drafts(
        self, client: TestClient, company: dict
    ) -> None:
        draft = _create_application(client, company["id"], job_title="Draft Role")
        applied = _create_application(
            client, company["id"], job_title="Applied Role",
            status="applied", date_applied="2024-06-01"
        )
        items = client.get("/api/v1/applications/").json()["items"]
        ids_in_order = [item["id"] for item in items]
        assert ids_in_order.index(applied["id"]) < ids_in_order.index(draft["id"])

    def test_default_sort_orders_applied_applications_by_date_desc(
        self, client: TestClient, company: dict
    ) -> None:
        older = _create_application(
            client, company["id"], job_title="Older Role",
            status="applied", date_applied="2024-01-01"
        )
        newer = _create_application(
            client, company["id"], job_title="Newer Role",
            status="applied", date_applied="2024-06-01"
        )
        items = client.get("/api/v1/applications/").json()["items"]
        ids = [item["id"] for item in items]
        assert ids.index(newer["id"]) < ids.index(older["id"])

    def test_returns_422_when_limit_exceeds_maximum(self, client: TestClient) -> None:
        resp = client.get("/api/v1/applications/?limit=101")
        assert resp.status_code == 422

    def test_returns_422_when_skip_is_negative(self, client: TestClient) -> None:
        resp = client.get("/api/v1/applications/?skip=-1")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/applications/{id}
# ---------------------------------------------------------------------------


class TestUpdateApplication:
    def test_updates_single_field_leaves_others_unchanged(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_application(
            client, company["id"], job_title="Engineer", location="NYC"
        )
        resp = client.patch(
            f"/api/v1/applications/{created['id']}",
            json={"status": "interview"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "interview"
        assert body["job_title"] == "Engineer"
        assert body["location"] == "NYC"

    def test_updates_date_applied(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_application(client, company["id"])
        resp = client.patch(
            f"/api/v1/applications/{created['id']}",
            json={"date_applied": "2024-07-15", "status": "applied"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["date_applied"] == "2024-07-15"
        assert body["status"] == "applied"

    def test_clears_nullable_field_by_sending_null(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_application(
            client, company["id"], location="NYC"
        )
        resp = client.patch(
            f"/api/v1/applications/{created['id']}",
            json={"location": None},
        )
        assert resp.status_code == 200
        assert resp.json()["location"] is None

    def test_reassigns_to_another_company(
        self, client: TestClient, company: dict, other_company: dict
    ) -> None:
        created = _create_application(client, company["id"])
        resp = client.patch(
            f"/api/v1/applications/{created['id']}",
            json={"company_id": other_company["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["company_id"] == other_company["id"]

    def test_returns_404_when_reassigning_to_nonexistent_company(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_application(client, company["id"])
        resp = client.patch(
            f"/api/v1/applications/{created['id']}",
            json={"company_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        resp = client.patch(
            f"/api/v1/applications/{uuid4()}", json={"location": "Remote"}
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/applications/{id}
# ---------------------------------------------------------------------------


class TestDeleteApplication:
    def test_returns_204_on_success(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_application(client, company["id"])
        resp = client.delete(f"/api/v1/applications/{created['id']}")
        assert resp.status_code == 204

    def test_application_is_not_retrievable_after_deletion(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_application(client, company["id"])
        client.delete(f"/api/v1/applications/{created['id']}")
        assert client.get(f"/api/v1/applications/{created['id']}").status_code == 404

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        resp = client.delete(f"/api/v1/applications/{uuid4()}")
        assert resp.status_code == 404
