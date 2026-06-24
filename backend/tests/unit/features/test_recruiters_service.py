from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.exceptions.http import ConflictError, NotFoundError, ValidationError
from app.features.recruiters.model import Recruiter
from app.features.recruiters.schema import RecruiterCreate, RecruiterUpdate
from app.features.recruiters.service import RecruiterService


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_company_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_repo: MagicMock, mock_company_repo: MagicMock) -> RecruiterService:
    svc = RecruiterService.__new__(RecruiterService)
    svc.repo = mock_repo
    svc.company_repo = mock_company_repo
    return svc


def _make_recruiter(**kwargs) -> Recruiter:
    defaults: dict = {
        "id": uuid4(),
        "company_id": None,
        "first_name": "Alice",
        "last_name": None,
        "email": None,
        "phone": None,
        "title": None,
        "linkedin_url": None,
        "notes": None,
    }
    return Recruiter(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestRecruiterServiceCreate:
    def test_creates_recruiter_with_email_only(
        self, service: RecruiterService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        mock_repo.get_by_email.return_value = None
        expected = _make_recruiter(first_name=None, email="alice@example.com")
        mock_repo.create.return_value = expected

        result = service.create(RecruiterCreate(email="alice@example.com"))

        mock_company_repo.get_or_raise.assert_not_called()
        mock_repo.get_by_email.assert_called_once_with("alice@example.com")
        mock_repo.create.assert_called_once()
        assert result is expected

    def test_creates_recruiter_with_first_name_only(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        expected = _make_recruiter(first_name="Alice")
        mock_repo.create.return_value = expected

        result = service.create(RecruiterCreate(first_name="Alice"))

        mock_repo.get_by_email.assert_not_called()
        assert result is expected

    def test_validates_company_when_company_id_provided(
        self, service: RecruiterService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        mock_company_repo.get_or_raise.return_value = MagicMock()
        mock_repo.create.return_value = _make_recruiter(company_id=company_id)

        service.create(RecruiterCreate(first_name="Alice", company_id=company_id))

        mock_company_repo.get_or_raise.assert_called_once_with(company_id)

    def test_raises_not_found_when_company_does_not_exist(
        self, service: RecruiterService, mock_company_repo: MagicMock
    ) -> None:
        mock_company_repo.get_or_raise.side_effect = NotFoundError("Company", uuid4())

        with pytest.raises(NotFoundError):
            service.create(RecruiterCreate(first_name="Alice", company_id=uuid4()))

    def test_raises_conflict_on_duplicate_email(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_email.return_value = _make_recruiter(email="alice@example.com")

        with pytest.raises(ConflictError):
            service.create(RecruiterCreate(email="alice@example.com"))

        mock_repo.create.assert_not_called()

    def test_skips_email_check_when_email_is_none(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        mock_repo.create.return_value = _make_recruiter()

        service.create(RecruiterCreate(first_name="Alice"))

        mock_repo.get_by_email.assert_not_called()


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


class TestRecruiterServiceGet:
    def test_returns_recruiter_when_found(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        recruiter_id = uuid4()
        expected = _make_recruiter(id=recruiter_id)
        mock_repo.get_or_raise.return_value = expected

        result = service.get(recruiter_id)

        mock_repo.get_or_raise.assert_called_once_with(recruiter_id)
        assert result is expected

    def test_propagates_not_found_from_repository(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("Recruiter", uuid4())

        with pytest.raises(NotFoundError):
            service.get(uuid4())


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class TestRecruiterServiceList:
    def test_delegates_all_filters_to_repository(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        mock_repo.list_paginated.return_value = ([], 0)

        service.list(query="alice", company_id=company_id, skip=5, limit=10)

        mock_repo.list_paginated.assert_called_once_with(
            query="alice",
            company_id=company_id,
            skip=5,
            limit=10,
        )

    def test_returns_items_and_total_from_repository(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        recruiters = [_make_recruiter(), _make_recruiter()]
        mock_repo.list_paginated.return_value = (recruiters, 2)

        items, total = service.list()

        assert items is recruiters
        assert total == 2


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestRecruiterServiceUpdate:
    def test_updates_single_field_without_touching_others(
        self, service: RecruiterService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter(first_name="Alice", title=None)
        updated = _make_recruiter(id=recruiter.id, first_name="Alice", title="Engineering")
        mock_repo.get_or_raise.return_value = recruiter
        mock_repo.update.return_value = updated

        result = service.update(recruiter.id, RecruiterUpdate(title="Engineering"))

        mock_company_repo.get_or_raise.assert_not_called()
        mock_repo.update.assert_called_once_with(recruiter, {"title": "Engineering"})
        assert result is updated

    def test_validates_company_when_company_id_changes(
        self, service: RecruiterService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter()
        new_company_id = uuid4()
        mock_repo.get_or_raise.return_value = recruiter
        mock_company_repo.get_or_raise.return_value = MagicMock()
        mock_repo.update.return_value = recruiter

        service.update(recruiter.id, RecruiterUpdate(company_id=new_company_id))

        mock_company_repo.get_or_raise.assert_called_once_with(new_company_id)

    def test_allows_detaching_company_by_sending_null(
        self, service: RecruiterService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter(company_id=uuid4())
        mock_repo.get_or_raise.return_value = recruiter
        mock_repo.update.return_value = recruiter

        service.update(recruiter.id, RecruiterUpdate(company_id=None))

        mock_company_repo.get_or_raise.assert_not_called()

    def test_raises_not_found_when_new_company_does_not_exist(
        self, service: RecruiterService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter()
        mock_repo.get_or_raise.return_value = recruiter
        mock_company_repo.get_or_raise.side_effect = NotFoundError("Company", uuid4())

        with pytest.raises(NotFoundError):
            service.update(recruiter.id, RecruiterUpdate(company_id=uuid4()))

    def test_raises_conflict_when_new_email_is_already_taken(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter(email="alice@example.com")
        mock_repo.get_or_raise.return_value = recruiter
        mock_repo.get_by_email.return_value = _make_recruiter(email="bob@example.com")

        with pytest.raises(ConflictError):
            service.update(recruiter.id, RecruiterUpdate(email="bob@example.com"))

        mock_repo.update.assert_not_called()

    def test_skips_email_conflict_check_when_email_is_unchanged(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter(email="alice@example.com")
        mock_repo.get_or_raise.return_value = recruiter
        mock_repo.update.return_value = recruiter

        # Sending the recruiter's existing email in a patch must not raise.
        service.update(recruiter.id, RecruiterUpdate(email="alice@example.com"))

        mock_repo.get_by_email.assert_not_called()

    def test_raises_validation_error_when_last_identifier_is_cleared(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        # Recruiter has only first_name set; clearing it leaves no identifier.
        recruiter = _make_recruiter(first_name="Alice", email=None, last_name=None)
        mock_repo.get_or_raise.return_value = recruiter

        with pytest.raises(ValidationError):
            service.update(recruiter.id, RecruiterUpdate(first_name=None))

        mock_repo.update.assert_not_called()

    def test_allows_clearing_one_identifier_when_another_remains(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter(first_name="Alice", email="alice@example.com")
        mock_repo.get_or_raise.return_value = recruiter
        mock_repo.update.return_value = recruiter

        # Clearing first_name is fine because email still identifies the recruiter.
        service.update(recruiter.id, RecruiterUpdate(first_name=None))

        mock_repo.update.assert_called_once()

    def test_propagates_not_found_when_recruiter_does_not_exist(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("Recruiter", uuid4())

        with pytest.raises(NotFoundError):
            service.update(uuid4(), RecruiterUpdate(title="Engineer"))


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestRecruiterServiceDelete:
    def test_deletes_existing_recruiter(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        recruiter = _make_recruiter()
        mock_repo.get_or_raise.return_value = recruiter

        service.delete(recruiter.id)

        mock_repo.delete.assert_called_once_with(recruiter)

    def test_propagates_not_found_from_repository(
        self, service: RecruiterService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("Recruiter", uuid4())

        with pytest.raises(NotFoundError):
            service.delete(uuid4())
