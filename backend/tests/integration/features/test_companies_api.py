from uuid import uuid4

from fastapi.testclient import TestClient


class TestCreateCompany:
    def test_returns_201_with_company_data(self, client: TestClient) -> None:
        response = client.post("/api/v1/companies/", json={"name": "Stripe"})
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Stripe"
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body
        assert body["website"] is None

    def test_returns_201_with_all_optional_fields(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/companies/",
            json={
                "name": "Anthropic",
                "website": "https://anthropic.com",
                "industry": "AI Safety",
                "location": "San Francisco",
                "notes": "Leading AI safety company.",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["website"] == "https://anthropic.com"
        assert body["industry"] == "AI Safety"
        assert body["location"] == "San Francisco"

    def test_returns_409_when_name_already_exists(self, client: TestClient) -> None:
        client.post("/api/v1/companies/", json={"name": "Stripe"})
        response = client.post("/api/v1/companies/", json={"name": "Stripe"})
        assert response.status_code == 409

    def test_returns_422_when_name_is_missing(self, client: TestClient) -> None:
        response = client.post("/api/v1/companies/", json={})
        assert response.status_code == 422

    def test_returns_422_when_name_is_empty_string(self, client: TestClient) -> None:
        response = client.post("/api/v1/companies/", json={"name": ""})
        assert response.status_code == 422

    def test_returns_422_when_name_is_only_whitespace(
        self, client: TestClient
    ) -> None:
        # str_strip_whitespace=True strips to "", then min_length=1 rejects it.
        response = client.post("/api/v1/companies/", json={"name": "   "})
        assert response.status_code == 422


class TestGetCompany:
    def test_returns_company_by_id(self, client: TestClient) -> None:
        created = client.post("/api/v1/companies/", json={"name": "Stripe"}).json()
        response = client.get(f"/api/v1/companies/{created['id']}")
        assert response.status_code == 200
        assert response.json()["name"] == "Stripe"

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        response = client.get(f"/api/v1/companies/{uuid4()}")
        assert response.status_code == 404

    def test_returns_422_for_invalid_uuid(self, client: TestClient) -> None:
        response = client.get("/api/v1/companies/not-a-uuid")
        assert response.status_code == 422


class TestListCompanies:
    def test_returns_empty_list_when_no_companies_exist(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/v1/companies/")
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_returns_all_companies_with_correct_total(
        self, client: TestClient
    ) -> None:
        client.post("/api/v1/companies/", json={"name": "Stripe"})
        client.post("/api/v1/companies/", json={"name": "Anthropic"})
        response = client.get("/api/v1/companies/")
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_search_filters_by_name_case_insensitively(
        self, client: TestClient
    ) -> None:
        client.post("/api/v1/companies/", json={"name": "Stripe"})
        client.post("/api/v1/companies/", json={"name": "Anthropic"})
        response = client.get("/api/v1/companies/?query=stripe")
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Stripe"

    def test_search_returns_partial_match(self, client: TestClient) -> None:
        client.post("/api/v1/companies/", json={"name": "Stripe"})
        client.post("/api/v1/companies/", json={"name": "Stripey Co"})
        client.post("/api/v1/companies/", json={"name": "Anthropic"})
        body = client.get("/api/v1/companies/?query=stripe").json()
        assert body["total"] == 2

    def test_pagination_returns_correct_page_size(
        self, client: TestClient
    ) -> None:
        for i in range(5):
            client.post("/api/v1/companies/", json={"name": f"Company {i:02d}"})
        body = client.get("/api/v1/companies/?skip=0&limit=2").json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        assert body["skip"] == 0
        assert body["limit"] == 2

    def test_pagination_pages_are_non_overlapping(
        self, client: TestClient
    ) -> None:
        for i in range(5):
            client.post("/api/v1/companies/", json={"name": f"Company {i:02d}"})
        first = {c["id"] for c in client.get("/api/v1/companies/?skip=0&limit=3").json()["items"]}
        second = {c["id"] for c in client.get("/api/v1/companies/?skip=3&limit=3").json()["items"]}
        assert first.isdisjoint(second)

    def test_returns_422_when_limit_exceeds_maximum(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/v1/companies/?limit=101")
        assert response.status_code == 422

    def test_returns_422_when_skip_is_negative(self, client: TestClient) -> None:
        response = client.get("/api/v1/companies/?skip=-1")
        assert response.status_code == 422


class TestUpdateCompany:
    def test_updates_single_field_leaves_others_unchanged(
        self, client: TestClient
    ) -> None:
        created = client.post(
            "/api/v1/companies/", json={"name": "Stripe", "industry": "Fintech"}
        ).json()
        response = client.patch(
            f"/api/v1/companies/{created['id']}", json={"location": "NYC"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["location"] == "NYC"
        assert body["name"] == "Stripe"
        assert body["industry"] == "Fintech"

    def test_allows_renaming_to_a_new_unique_name(
        self, client: TestClient
    ) -> None:
        created = client.post("/api/v1/companies/", json={"name": "Stripe"}).json()
        response = client.patch(
            f"/api/v1/companies/{created['id']}", json={"name": "Stripe Inc"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Stripe Inc"

    def test_returns_409_when_renaming_to_an_existing_name(
        self, client: TestClient
    ) -> None:
        client.post("/api/v1/companies/", json={"name": "Stripe"})
        other = client.post("/api/v1/companies/", json={"name": "Anthropic"}).json()
        response = client.patch(
            f"/api/v1/companies/{other['id']}", json={"name": "Stripe"}
        )
        assert response.status_code == 409

    def test_returns_200_when_name_is_unchanged(self, client: TestClient) -> None:
        created = client.post("/api/v1/companies/", json={"name": "Stripe"}).json()
        response = client.patch(
            f"/api/v1/companies/{created['id']}", json={"name": "Stripe"}
        )
        assert response.status_code == 200

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        response = client.patch(
            f"/api/v1/companies/{uuid4()}", json={"location": "NYC"}
        )
        assert response.status_code == 404


class TestDeleteCompany:
    def test_returns_204_on_success(self, client: TestClient) -> None:
        created = client.post("/api/v1/companies/", json={"name": "Stripe"}).json()
        response = client.delete(f"/api/v1/companies/{created['id']}")
        assert response.status_code == 204

    def test_company_is_not_retrievable_after_deletion(
        self, client: TestClient
    ) -> None:
        created = client.post("/api/v1/companies/", json={"name": "Stripe"}).json()
        client.delete(f"/api/v1/companies/{created['id']}")
        assert client.get(f"/api/v1/companies/{created['id']}").status_code == 404

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        response = client.delete(f"/api/v1/companies/{uuid4()}")
        assert response.status_code == 404
