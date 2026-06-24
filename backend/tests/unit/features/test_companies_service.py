from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.exceptions.http import ConflictError, NotFoundError
from app.features.companies.model import Company
from app.features.companies.schema import CompanyCreate, CompanyUpdate
from app.features.companies.service import CompanyService


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_repo: MagicMock) -> CompanyService:
    # Bypass __init__ so we can inject the mock repository directly.
    svc = CompanyService.__new__(CompanyService)
    svc.repo = mock_repo
    return svc


class TestCompanyServiceCreate:
    def test_creates_company_when_name_is_unique(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_name.return_value = None
        expected = Company(id=uuid4(), name="Stripe")
        mock_repo.create.return_value = expected

        result = service.create(CompanyCreate(name="Stripe"))

        mock_repo.get_by_name.assert_called_once_with("Stripe")
        mock_repo.create.assert_called_once()
        assert result is expected

    def test_raises_conflict_when_name_already_exists(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_name.return_value = Company(id=uuid4(), name="Stripe")

        with pytest.raises(ConflictError):
            service.create(CompanyCreate(name="Stripe"))

        mock_repo.create.assert_not_called()


class TestCompanyServiceGet:
    def test_returns_company_when_found(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        expected = Company(id=company_id, name="Stripe")
        mock_repo.get_or_raise.return_value = expected

        result = service.get(company_id)

        mock_repo.get_or_raise.assert_called_once_with(company_id)
        assert result is expected

    def test_propagates_not_found_from_repository(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("Company", uuid4())

        with pytest.raises(NotFoundError):
            service.get(uuid4())


class TestCompanyServiceUpdate:
    def test_updates_fields_and_skips_conflict_check_when_name_omitted(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        company = Company(id=company_id, name="Stripe")
        updated = Company(id=company_id, name="Stripe", location="NYC")
        mock_repo.get_or_raise.return_value = company
        mock_repo.update.return_value = updated

        result = service.update(company_id, CompanyUpdate(location="NYC"))

        mock_repo.get_by_name.assert_not_called()
        mock_repo.update.assert_called_once_with(company, {"location": "NYC"})
        assert result is updated

    def test_raises_conflict_when_new_name_is_taken_by_another_company(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        company = Company(id=company_id, name="Stripe")
        mock_repo.get_or_raise.return_value = company
        mock_repo.get_by_name.return_value = Company(id=uuid4(), name="Anthropic")

        with pytest.raises(ConflictError):
            service.update(company_id, CompanyUpdate(name="Anthropic"))

        mock_repo.update.assert_not_called()

    def test_skips_conflict_check_when_name_is_unchanged(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        company = Company(id=company_id, name="Stripe")
        mock_repo.get_or_raise.return_value = company
        mock_repo.update.return_value = company

        service.update(company_id, CompanyUpdate(name="Stripe"))

        mock_repo.get_by_name.assert_not_called()
        mock_repo.update.assert_called_once()

    def test_propagates_not_found_from_repository(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("Company", uuid4())

        with pytest.raises(NotFoundError):
            service.update(uuid4(), CompanyUpdate(location="NYC"))


class TestCompanyServiceDelete:
    def test_deletes_existing_company(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        company = Company(id=uuid4(), name="Stripe")
        mock_repo.get_or_raise.return_value = company

        service.delete(company.id)

        mock_repo.delete.assert_called_once_with(company)

    def test_propagates_not_found_from_repository(
        self, service: CompanyService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("Company", uuid4())

        with pytest.raises(NotFoundError):
            service.delete(uuid4())
