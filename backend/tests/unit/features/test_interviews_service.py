from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.exceptions.http import NotFoundError
from app.features.interviews.model import Interview, InterviewStatus, InterviewType
from app.features.interviews.schema import InterviewCreate, InterviewUpdate
from app.features.interviews.service import InterviewService

_NOW = datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc)
USER_ID = uuid4()


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_application_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_recruiter_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(
    mock_repo: MagicMock,
    mock_application_repo: MagicMock,
    mock_recruiter_repo: MagicMock,
) -> InterviewService:
    svc = InterviewService.__new__(InterviewService)
    svc.user_id = USER_ID
    svc.repo = mock_repo
    svc.application_repo = mock_application_repo
    svc.recruiter_repo = mock_recruiter_repo
    return svc


def _make_interview(**kwargs) -> Interview:
    defaults: dict = {
        "id": uuid4(),
        "application_id": uuid4(),
        "recruiter_id": None,
        "interview_type": None,
        "scheduled_at": _NOW,
        "duration_minutes": 30,
        "location": None,
        "meeting_link": None,
        "status": InterviewStatus.SCHEDULED.value,
        "notes": None,
        "feedback": None,
    }
    return Interview(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestInterviewServiceCreate:
    def test_creates_interview_when_application_exists(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        application_id = uuid4()
        mock_application_repo.get_or_raise_for_user.return_value = MagicMock()
        expected = _make_interview(application_id=application_id)
        mock_repo.create.return_value = expected

        result = service.create(
            InterviewCreate(application_id=application_id, scheduled_at=_NOW)
        )

        mock_application_repo.get_or_raise_for_user.assert_called_once_with(
            application_id, USER_ID
        )
        mock_repo.create.assert_called_once()
        assert mock_repo.create.call_args[0][0]["user_id"] == USER_ID
        assert result is expected

    def test_raises_not_found_when_application_does_not_exist(
        self,
        service: InterviewService,
        mock_application_repo: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        mock_application_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "JobApplication", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.create(
                InterviewCreate(application_id=uuid4(), scheduled_at=_NOW)
            )

        mock_repo.create.assert_not_called()

    def test_validates_recruiter_when_recruiter_id_provided(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        recruiter_id = uuid4()
        mock_application_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_recruiter_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_repo.create.return_value = _make_interview(recruiter_id=recruiter_id)

        service.create(
            InterviewCreate(
                application_id=uuid4(),
                recruiter_id=recruiter_id,
                scheduled_at=_NOW,
            )
        )

        mock_recruiter_repo.get_or_raise_for_user.assert_called_once_with(
            recruiter_id, USER_ID
        )

    def test_raises_not_found_when_recruiter_does_not_exist(
        self,
        service: InterviewService,
        mock_application_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        mock_application_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_recruiter_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "Recruiter", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.create(
                InterviewCreate(
                    application_id=uuid4(),
                    recruiter_id=uuid4(),
                    scheduled_at=_NOW,
                )
            )

        mock_repo.create.assert_not_called()

    def test_skips_recruiter_check_when_recruiter_id_is_none(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        mock_application_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_repo.create.return_value = _make_interview()

        service.create(InterviewCreate(application_id=uuid4(), scheduled_at=_NOW))

        mock_recruiter_repo.get_or_raise_for_user.assert_not_called()

    def test_status_defaults_to_scheduled(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        mock_application_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_repo.create.return_value = _make_interview()

        service.create(InterviewCreate(application_id=uuid4(), scheduled_at=_NOW))

        call_data = mock_repo.create.call_args[0][0]
        assert call_data["status"] == InterviewStatus.SCHEDULED

    def test_duration_defaults_to_30(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        mock_application_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_repo.create.return_value = _make_interview()

        service.create(InterviewCreate(application_id=uuid4(), scheduled_at=_NOW))

        call_data = mock_repo.create.call_args[0][0]
        assert call_data["duration_minutes"] == 30


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


class TestInterviewServiceGet:
    def test_returns_interview_when_found(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        interview_id = uuid4()
        expected = _make_interview(id=interview_id)
        mock_repo.get_or_raise_for_user.return_value = expected

        result = service.get(interview_id)

        mock_repo.get_or_raise_for_user.assert_called_once_with(interview_id, USER_ID)
        assert result is expected

    def test_propagates_not_found_from_repository(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise_for_user.side_effect = NotFoundError("Interview", uuid4())

        with pytest.raises(NotFoundError):
            service.get(uuid4())


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class TestInterviewServiceList:
    def test_delegates_all_filters_to_repository(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        application_id = uuid4()
        recruiter_id = uuid4()
        mock_repo.list_paginated.return_value = ([], 0)

        service.list(
            application_id=application_id,
            recruiter_id=recruiter_id,
            status=InterviewStatus.COMPLETED,
            interview_type=InterviewType.TECHNICAL,
            skip=5,
            limit=10,
        )

        mock_repo.list_paginated.assert_called_once_with(
            application_id=application_id,
            recruiter_id=recruiter_id,
            status=InterviewStatus.COMPLETED,
            interview_type=InterviewType.TECHNICAL,
            user_id=USER_ID,
            skip=5,
            limit=10,
        )

    def test_returns_items_and_total_from_repository(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        interviews = [_make_interview(), _make_interview()]
        mock_repo.list_paginated.return_value = (interviews, 2)

        items, total = service.list()

        assert items is interviews
        assert total == 2


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestInterviewServiceUpdate:
    def test_updates_single_field_leaves_others_unchanged(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        interview = _make_interview(status=InterviewStatus.SCHEDULED.value)
        updated = _make_interview(id=interview.id, status=InterviewStatus.COMPLETED.value)
        mock_repo.get_or_raise_for_user.return_value = interview
        mock_repo.update.return_value = updated

        result = service.update(
            interview.id, InterviewUpdate(status=InterviewStatus.COMPLETED)
        )

        mock_application_repo.get_or_raise_for_user.assert_not_called()
        mock_recruiter_repo.get_or_raise_for_user.assert_not_called()
        mock_repo.update.assert_called_once_with(
            interview, {"status": InterviewStatus.COMPLETED}
        )
        assert result is updated

    def test_validates_application_when_application_id_changes(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        interview = _make_interview()
        new_application_id = uuid4()
        mock_repo.get_or_raise_for_user.return_value = interview
        mock_application_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_repo.update.return_value = interview

        service.update(
            interview.id, InterviewUpdate(application_id=new_application_id)
        )

        mock_application_repo.get_or_raise_for_user.assert_called_once_with(
            new_application_id, USER_ID
        )

    def test_validates_recruiter_when_recruiter_id_changes(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        interview = _make_interview()
        new_recruiter_id = uuid4()
        mock_repo.get_or_raise_for_user.return_value = interview
        mock_recruiter_repo.get_or_raise_for_user.return_value = MagicMock()
        mock_repo.update.return_value = interview

        service.update(
            interview.id, InterviewUpdate(recruiter_id=new_recruiter_id)
        )

        mock_recruiter_repo.get_or_raise_for_user.assert_called_once_with(
            new_recruiter_id, USER_ID
        )

    def test_allows_detaching_recruiter_by_sending_null(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        interview = _make_interview(recruiter_id=uuid4())
        mock_repo.get_or_raise_for_user.return_value = interview
        mock_repo.update.return_value = interview

        service.update(interview.id, InterviewUpdate(recruiter_id=None))

        mock_recruiter_repo.get_or_raise_for_user.assert_not_called()

    def test_raises_not_found_when_new_application_does_not_exist(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        interview = _make_interview()
        mock_repo.get_or_raise_for_user.return_value = interview
        mock_application_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "JobApplication", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.update(interview.id, InterviewUpdate(application_id=uuid4()))

    def test_raises_not_found_when_new_recruiter_does_not_exist(
        self,
        service: InterviewService,
        mock_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        interview = _make_interview()
        mock_repo.get_or_raise_for_user.return_value = interview
        mock_recruiter_repo.get_or_raise_for_user.side_effect = NotFoundError(
            "Recruiter", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.update(interview.id, InterviewUpdate(recruiter_id=uuid4()))

    def test_propagates_not_found_when_interview_does_not_exist(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise_for_user.side_effect = NotFoundError("Interview", uuid4())

        with pytest.raises(NotFoundError):
            service.update(uuid4(), InterviewUpdate(status=InterviewStatus.COMPLETED))


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestInterviewServiceDelete:
    def test_deletes_existing_interview(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        interview = _make_interview()
        mock_repo.get_or_raise_for_user.return_value = interview

        service.delete(interview.id)

        mock_repo.delete.assert_called_once_with(interview)

    def test_propagates_not_found_from_repository(
        self, service: InterviewService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise_for_user.side_effect = NotFoundError("Interview", uuid4())

        with pytest.raises(NotFoundError):
            service.delete(uuid4())
