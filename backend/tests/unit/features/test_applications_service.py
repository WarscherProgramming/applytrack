from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.exceptions.http import NotFoundError
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.applications.schema import ApplicationCreate, ApplicationUpdate
from app.features.applications.service import ApplicationService

USER_ID = uuid4()


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_company_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_repo: MagicMock, mock_company_repo: MagicMock) -> ApplicationService:
    # Bypass __init__ to inject both mock repositories directly.
    svc = ApplicationService.__new__(ApplicationService)
    svc.user_id = USER_ID
    svc.repo = mock_repo
    svc.company_repo = mock_company_repo
    svc.resume_repo = MagicMock()
    svc.cover_letter_repo = MagicMock()
    return svc


def _make_application(**kwargs) -> JobApplication:
    defaults = {
        "id": uuid4(),
        "company_id": uuid4(),
        "job_title": "Software Engineer",
        "status": ApplicationStatus.DRAFT.value,
    }
    return JobApplication(**{**defaults, **kwargs})


class TestApplicationServiceCreate:
    def test_creates_application_when_company_exists(
        self, service: ApplicationService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        mock_company_repo.get_or_raise_for_user.return_value = MagicMock()
        expected = _make_application(company_id=company_id)
        mock_repo.create.return_value = expected

        result = service.create(
            ApplicationCreate(company_id=company_id, job_title="Software Engineer")
        )

        mock_company_repo.get_or_raise_for_user.assert_called_once_with(
            company_id, USER_ID
        )
        mock_repo.create.assert_called_once()
        assert mock_repo.create.call_args[0][0]["user_id"] == USER_ID
        assert result is expected

    def test_raises_not_found_when_company_does_not_exist(
        self, service: ApplicationService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        mock_company_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "Company", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.create(
                ApplicationCreate(company_id=uuid4(), job_title="Software Engineer")
            )

        mock_repo.create.assert_not_called()

    def test_status_defaults_to_draft(
        self, service: ApplicationService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        mock_company_repo.get_or_raise_for_user.return_value = MagicMock()
        expected = _make_application()
        mock_repo.create.return_value = expected

        service.create(
            ApplicationCreate(company_id=uuid4(), job_title="Backend Engineer")
        )

        call_data = mock_repo.create.call_args[0][0]
        assert call_data["status"] == ApplicationStatus.DRAFT


class TestApplicationServiceGet:
    def test_returns_application_when_found(
        self, service: ApplicationService, mock_repo: MagicMock
    ) -> None:
        application_id = uuid4()
        expected = _make_application(id=application_id)
        mock_repo.get_or_raise_for_user.return_value = expected

        result = service.get(application_id)

        mock_repo.get_or_raise_for_user.assert_called_once_with(
            application_id, USER_ID
        )
        assert result is expected

    def test_propagates_not_found_from_repository(
        self, service: ApplicationService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "JobApplication", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.get(uuid4())


class TestApplicationServiceList:
    def test_delegates_all_filters_to_repository(
        self, service: ApplicationService, mock_repo: MagicMock
    ) -> None:
        company_id = uuid4()
        mock_repo.list_paginated.return_value = ([], 0)

        service.list(
            query="engineer",
            status=ApplicationStatus.APPLIED,
            company_id=company_id,
            skip=10,
            limit=5,
        )

        mock_repo.list_paginated.assert_called_once_with(
            query="engineer",
            status=ApplicationStatus.APPLIED,
            company_id=company_id,
            user_id=USER_ID,
            skip=10,
            limit=5,
        )

    def test_returns_items_and_total_from_repository(
        self, service: ApplicationService, mock_repo: MagicMock
    ) -> None:
        applications = [_make_application(), _make_application()]
        mock_repo.list_paginated.return_value = (applications, 2)

        items, total = service.list()

        assert items is applications
        assert total == 2


class TestApplicationServiceUpdate:
    def test_updates_fields_without_touching_company_when_company_id_omitted(
        self, service: ApplicationService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        application = _make_application()
        updated = _make_application(id=application.id, status=ApplicationStatus.APPLIED.value)
        mock_repo.get_or_raise_for_user.return_value = application
        mock_repo.update.return_value = updated

        result = service.update(application.id, ApplicationUpdate(status=ApplicationStatus.APPLIED))

        mock_company_repo.get_or_raise_for_user.assert_not_called()
        mock_repo.update.assert_called_once_with(
            application, {"status": ApplicationStatus.APPLIED}
        )
        assert result is updated

    def test_validates_new_company_when_company_id_changes(
        self, service: ApplicationService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        application = _make_application()
        new_company_id = uuid4()
        mock_repo.get_or_raise_for_user.return_value = application
        mock_company_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_repo.update.return_value = application

        service.update(application.id, ApplicationUpdate(company_id=new_company_id))

        mock_company_repo.get_or_raise_for_user.assert_called_once_with(
            new_company_id, USER_ID
        )

    def test_raises_not_found_when_new_company_does_not_exist(
        self, service: ApplicationService, mock_repo: MagicMock, mock_company_repo: MagicMock
    ) -> None:
        application = _make_application()
        mock_repo.get_or_raise_for_user.return_value = application
        mock_company_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "Company", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.update(application.id, ApplicationUpdate(company_id=uuid4()))

        mock_repo.update.assert_not_called()

    def test_propagates_not_found_when_application_does_not_exist(
        self, service: ApplicationService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "JobApplication", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.update(uuid4(), ApplicationUpdate(location="Remote"))


class TestApplicationServiceDelete:
    def test_deletes_existing_application(
        self, service: ApplicationService, mock_repo: MagicMock
    ) -> None:
        application = _make_application()
        mock_repo.get_or_raise_for_user.return_value = application

        service.delete(application.id)

        mock_repo.delete.assert_called_once_with(application)

    def test_propagates_not_found_from_repository(
        self, service: ApplicationService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "JobApplication", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.delete(uuid4())
