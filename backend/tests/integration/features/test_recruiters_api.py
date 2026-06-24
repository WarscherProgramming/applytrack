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


def _create_recruiter(client: TestClient, **kwargs) -> dict:
    # Default payload satisfies the "at least one identifier" rule.
    payload = {"first_name": "Alice", **kwargs}
    resp = client.post("/api/v1/recruiters/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /api/v1/recruiters/
# ---------------------------------------------------------------------------


class TestCreateRecruiter:
    def test_returns_201_with_all_fields(
        self, client: TestClient, company: dict
    ) -> None:
        resp = client.post(
            "/api/v1/recruiters/",
            json={
                "company_id": company["id"],
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "phone": "+1-555-0100",
                "title": "Technical Recruiter",
                "linkedin_url": "https://linkedin.com/in/alice",
                "notes": "Met at PyCon.",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["company_id"] == company["id"]
        assert body["first_name"] == "Alice"
        assert body["last_name"] == "Smith"
        assert body["email"] == "alice@example.com"
        assert body["phone"] == "+1-555-0100"
        assert body["title"] == "Technical Recruiter"
        assert body["linkedin_url"] == "https://linkedin.com/in/alice"
        assert body["notes"] == "Met at PyCon."
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_returns_201_with_first_name_only(self, client: TestClient) -> None:
        resp = client.post("/api/v1/recruiters/", json={"first_name": "Bob"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["first_name"] == "Bob"
        assert body["company_id"] is None
        assert body["email"] is None

    def test_returns_201_with_email_only(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/recruiters/", json={"email": "only@example.com"}
        )
        assert resp.status_code == 201
        assert resp.json()["email"] == "only@example.com"

    def test_returns_201_with_last_name_only(self, client: TestClient) -> None:
        resp = client.post("/api/v1/recruiters/", json={"last_name": "Jones"})
        assert resp.status_code == 201
        assert resp.json()["last_name"] == "Jones"

    def test_optional_fields_are_null_when_omitted(self, client: TestClient) -> None:
        body = _create_recruiter(client)
        assert body["company_id"] is None
        assert body["last_name"] is None
        assert body["email"] is None
        assert body["phone"] is None
        assert body["title"] is None
        assert body["linkedin_url"] is None
        assert body["notes"] is None

    def test_returns_404_when_company_does_not_exist(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/api/v1/recruiters/",
            json={"first_name": "Alice", "company_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_returns_409_on_duplicate_email(self, client: TestClient) -> None:
        client.post("/api/v1/recruiters/", json={"email": "dup@example.com"})
        resp = client.post(
            "/api/v1/recruiters/", json={"first_name": "Alice", "email": "dup@example.com"}
        )
        assert resp.status_code == 409

    def test_returns_422_when_no_identifier_provided(self, client: TestClient) -> None:
        resp = client.post("/api/v1/recruiters/", json={"title": "Recruiter"})
        assert resp.status_code == 422

    def test_returns_422_on_invalid_email(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/recruiters/", json={"first_name": "Alice", "email": "not-an-email"}
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/recruiters/{id}
# ---------------------------------------------------------------------------


class TestGetRecruiter:
    def test_returns_recruiter_by_id(self, client: TestClient) -> None:
        created = _create_recruiter(client, first_name="Carol")
        resp = client.get(f"/api/v1/recruiters/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Carol"

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        assert client.get(f"/api/v1/recruiters/{uuid4()}").status_code == 404

    def test_returns_422_for_invalid_uuid(self, client: TestClient) -> None:
        assert client.get("/api/v1/recruiters/not-a-uuid").status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/recruiters/
# ---------------------------------------------------------------------------


class TestListRecruiters:
    def test_returns_empty_list_when_no_recruiters_exist(
        self, client: TestClient
    ) -> None:
        resp = client.get("/api/v1/recruiters/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_returns_all_recruiters_with_correct_total(
        self, client: TestClient
    ) -> None:
        _create_recruiter(client, first_name="Alice")
        _create_recruiter(client, last_name="Bob")
        body = client.get("/api/v1/recruiters/").json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_search_matches_first_name(self, client: TestClient) -> None:
        _create_recruiter(client, first_name="Alice")
        _create_recruiter(client, first_name="Bob")
        body = client.get("/api/v1/recruiters/?query=alice").json()
        assert body["total"] == 1
        assert body["items"][0]["first_name"] == "Alice"

    def test_search_matches_last_name(self, client: TestClient) -> None:
        _create_recruiter(client, first_name="A", last_name="Smith")
        _create_recruiter(client, first_name="B", last_name="Jones")
        body = client.get("/api/v1/recruiters/?query=smith").json()
        assert body["total"] == 1
        assert body["items"][0]["last_name"] == "Smith"

    def test_search_matches_email(self, client: TestClient) -> None:
        _create_recruiter(client, email="recruiter@acme.com")
        _create_recruiter(client, first_name="Bob", email="recruiter@other.com")
        body = client.get("/api/v1/recruiters/?query=acme").json()
        assert body["total"] == 1
        assert body["items"][0]["email"] == "recruiter@acme.com"

    def test_search_matches_title(self, client: TestClient) -> None:
        _create_recruiter(client, first_name="A", title="Technical Recruiter")
        _create_recruiter(client, first_name="B", title="Engineering Manager")
        body = client.get("/api/v1/recruiters/?query=technical").json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "Technical Recruiter"

    def test_search_is_case_insensitive(self, client: TestClient) -> None:
        _create_recruiter(client, first_name="Alice")
        body = client.get("/api/v1/recruiters/?query=ALICE").json()
        assert body["total"] == 1

    def test_filter_by_company_id_returns_only_that_companys_recruiters(
        self, client: TestClient, company: dict, other_company: dict
    ) -> None:
        _create_recruiter(client, first_name="A", company_id=company["id"])
        _create_recruiter(client, first_name="B", company_id=company["id"])
        _create_recruiter(client, first_name="C", company_id=other_company["id"])
        body = client.get(f"/api/v1/recruiters/?company_id={company['id']}").json()
        assert body["total"] == 2
        assert all(item["company_id"] == company["id"] for item in body["items"])

    def test_pagination_returns_correct_page_size(self, client: TestClient) -> None:
        for i in range(5):
            _create_recruiter(client, first_name=f"Recruiter{i:02d}")
        body = client.get("/api/v1/recruiters/?skip=0&limit=2").json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 2

    def test_pagination_pages_are_non_overlapping(self, client: TestClient) -> None:
        for i in range(5):
            _create_recruiter(client, first_name=f"Recruiter{i:02d}")
        first = {r["id"] for r in client.get("/api/v1/recruiters/?skip=0&limit=3").json()["items"]}
        second = {r["id"] for r in client.get("/api/v1/recruiters/?skip=3&limit=3").json()["items"]}
        assert first.isdisjoint(second)

    def test_list_includes_all_created_records(self, client: TestClient) -> None:
        # Sort order by created_at DESC is correct in production, but within
        # a test transaction every row gets the same created_at (PostgreSQL's
        # now() returns transaction start time), so we only verify presence.
        first = _create_recruiter(client, first_name="First")
        second = _create_recruiter(client, first_name="Second")
        body = client.get("/api/v1/recruiters/").json()
        ids = {item["id"] for item in body["items"]}
        assert first["id"] in ids
        assert second["id"] in ids

    def test_returns_422_when_limit_exceeds_maximum(self, client: TestClient) -> None:
        assert client.get("/api/v1/recruiters/?limit=101").status_code == 422

    def test_returns_422_when_skip_is_negative(self, client: TestClient) -> None:
        assert client.get("/api/v1/recruiters/?skip=-1").status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/recruiters/{id}
# ---------------------------------------------------------------------------


class TestUpdateRecruiter:
    def test_updates_single_field_leaves_others_unchanged(
        self, client: TestClient
    ) -> None:
        created = _create_recruiter(client, first_name="Alice", title="Recruiter")
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}", json={"last_name": "Smith"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["first_name"] == "Alice"
        assert body["last_name"] == "Smith"
        assert body["title"] == "Recruiter"

    def test_clears_nullable_field_by_sending_null(self, client: TestClient) -> None:
        created = _create_recruiter(client, first_name="Alice", title="Recruiter")
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}", json={"title": None}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] is None

    def test_assigns_recruiter_to_company(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_recruiter(client)
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}",
            json={"company_id": company["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["company_id"] == company["id"]

    def test_detaches_recruiter_from_company_by_sending_null(
        self, client: TestClient, company: dict
    ) -> None:
        created = _create_recruiter(client, company_id=company["id"])
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}", json={"company_id": None}
        )
        assert resp.status_code == 200
        assert resp.json()["company_id"] is None

    def test_reassigns_to_another_company(
        self, client: TestClient, company: dict, other_company: dict
    ) -> None:
        created = _create_recruiter(client, company_id=company["id"])
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}",
            json={"company_id": other_company["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["company_id"] == other_company["id"]

    def test_returns_404_when_new_company_does_not_exist(
        self, client: TestClient
    ) -> None:
        created = _create_recruiter(client)
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}",
            json={"company_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_returns_409_when_new_email_is_already_taken(
        self, client: TestClient
    ) -> None:
        _create_recruiter(client, first_name="Bob", email="taken@example.com")
        alice = _create_recruiter(client, first_name="Alice")
        resp = client.patch(
            f"/api/v1/recruiters/{alice['id']}",
            json={"email": "taken@example.com"},
        )
        assert resp.status_code == 409

    def test_allows_patching_own_email_without_conflict(
        self, client: TestClient
    ) -> None:
        created = _create_recruiter(client, email="me@example.com")
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}",
            json={"email": "me@example.com", "title": "Updated"},
        )
        assert resp.status_code == 200

    def test_returns_422_when_clearing_last_identifier(
        self, client: TestClient
    ) -> None:
        # Create recruiter with only a first_name, then try to clear it.
        created = _create_recruiter(client, first_name="Solo")
        resp = client.patch(
            f"/api/v1/recruiters/{created['id']}", json={"first_name": None}
        )
        assert resp.status_code == 422

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        resp = client.patch(
            f"/api/v1/recruiters/{uuid4()}", json={"title": "Recruiter"}
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/recruiters/{id}
# ---------------------------------------------------------------------------


class TestDeleteRecruiter:
    def test_returns_204_on_success(self, client: TestClient) -> None:
        created = _create_recruiter(client)
        resp = client.delete(f"/api/v1/recruiters/{created['id']}")
        assert resp.status_code == 204

    def test_recruiter_is_not_retrievable_after_deletion(
        self, client: TestClient
    ) -> None:
        created = _create_recruiter(client)
        client.delete(f"/api/v1/recruiters/{created['id']}")
        assert client.get(f"/api/v1/recruiters/{created['id']}").status_code == 404

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        assert client.delete(f"/api/v1/recruiters/{uuid4()}").status_code == 404
