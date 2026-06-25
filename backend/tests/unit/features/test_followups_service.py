from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.exceptions.http import NotFoundError
from app.features.followups.model import (
    FollowUp,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)
from app.features.followups.schema import FollowUpCreate, FollowUpUpdate
from app.features.followups.service import FollowUpService

_DUE = date(2024, 6, 15)
_STAMP = datetime(2024, 6, 10, 12, 0, 0, tzinfo=timezone.utc)


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
def mock_interview_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(
    mock_repo: MagicMock,
    mock_application_repo: MagicMock,
    mock_recruiter_repo: MagicMock,
    mock_interview_repo: MagicMock,
) -> FollowUpService:
    svc = FollowUpService.__new__(FollowUpService)
    svc.repo = mock_repo
    svc.application_repo = mock_application_repo
    svc.recruiter_repo = mock_recruiter_repo
    svc.interview_repo = mock_interview_repo
    return svc


def _make_followup(**kwargs) -> FollowUp:
    defaults: dict = {
        "id": uuid4(),
        "application_id": uuid4(),
        "recruiter_id": None,
        "interview_id": None,
        "title": "Send thank-you note",
        "description": None,
        "followup_type": FollowUpType.EMAIL.value,
        "status": FollowUpStatus.PENDING.value,
        "priority": FollowUpPriority.MEDIUM.value,
        "due_date": _DUE,
        "completed_at": None,
    }
    return FollowUp(**{**defaults, **kwargs})


def _create_data(**kwargs) -> FollowUpCreate:
    defaults: dict = {
        "application_id": uuid4(),
        "title": "Send thank-you note",
        "followup_type": FollowUpType.EMAIL,
        "due_date": _DUE,
    }
    return FollowUpCreate(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestFollowUpServiceCreate:
    def test_creates_followup_when_application_exists(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        application_id = uuid4()
        mock_application_repo.get_or_raise.return_value = MagicMock()
        expected = _make_followup(application_id=application_id)
        mock_repo.create.return_value = expected

        result = service.create(_create_data(application_id=application_id))

        mock_application_repo.get_or_raise.assert_called_once_with(application_id)
        mock_repo.create.assert_called_once()
        assert result is expected

    def test_raises_not_found_when_application_does_not_exist(
        self,
        service: FollowUpService,
        mock_application_repo: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        mock_application_repo.get_or_raise.side_effect = NotFoundError(
            "JobApplication", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.create(_create_data())

        mock_repo.create.assert_not_called()

    def test_validates_recruiter_when_provided(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        recruiter_id = uuid4()
        mock_recruiter_repo.get_or_raise.return_value = MagicMock()
        mock_repo.create.return_value = _make_followup(recruiter_id=recruiter_id)

        service.create(_create_data(recruiter_id=recruiter_id))

        mock_recruiter_repo.get_or_raise.assert_called_once_with(recruiter_id)

    def test_validates_interview_when_provided(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_interview_repo: MagicMock,
    ) -> None:
        interview_id = uuid4()
        mock_interview_repo.get_or_raise.return_value = MagicMock()
        mock_repo.create.return_value = _make_followup(interview_id=interview_id)

        service.create(_create_data(interview_id=interview_id))

        mock_interview_repo.get_or_raise.assert_called_once_with(interview_id)

    def test_raises_not_found_when_recruiter_does_not_exist(
        self,
        service: FollowUpService,
        mock_recruiter_repo: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        mock_recruiter_repo.get_or_raise.side_effect = NotFoundError(
            "Recruiter", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.create(_create_data(recruiter_id=uuid4()))

        mock_repo.create.assert_not_called()

    def test_raises_not_found_when_interview_does_not_exist(
        self,
        service: FollowUpService,
        mock_interview_repo: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        mock_interview_repo.get_or_raise.side_effect = NotFoundError(
            "Interview", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.create(_create_data(interview_id=uuid4()))

        mock_repo.create.assert_not_called()

    def test_skips_optional_fk_checks_when_not_provided(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
        mock_interview_repo: MagicMock,
    ) -> None:
        mock_repo.create.return_value = _make_followup()

        service.create(_create_data())

        mock_recruiter_repo.get_or_raise.assert_not_called()
        mock_interview_repo.get_or_raise.assert_not_called()

    def test_defaults_status_pending_and_priority_medium(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.create.return_value = _make_followup()

        service.create(_create_data())

        payload = mock_repo.create.call_args[0][0]
        assert payload["status"] == FollowUpStatus.PENDING
        assert payload["priority"] == FollowUpPriority.MEDIUM

    def test_completed_at_auto_populated_when_created_completed(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.create.return_value = _make_followup()

        service.create(_create_data(status=FollowUpStatus.COMPLETED))

        payload = mock_repo.create.call_args[0][0]
        assert payload["completed_at"] is not None

    def test_explicit_completed_at_respected_on_create(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.create.return_value = _make_followup()

        service.create(
            _create_data(status=FollowUpStatus.COMPLETED, completed_at=_STAMP)
        )

        payload = mock_repo.create.call_args[0][0]
        assert payload["completed_at"] == _STAMP

    def test_completed_at_stays_null_when_status_pending(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.create.return_value = _make_followup()

        service.create(_create_data())

        payload = mock_repo.create.call_args[0][0]
        assert payload["completed_at"] is None


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


class TestFollowUpServiceGet:
    def test_returns_followup_when_found(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        followup_id = uuid4()
        expected = _make_followup(id=followup_id)
        mock_repo.get_or_raise.return_value = expected

        result = service.get(followup_id)

        mock_repo.get_or_raise.assert_called_once_with(followup_id)
        assert result is expected

    def test_propagates_not_found_from_repository(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("FollowUp", uuid4())

        with pytest.raises(NotFoundError):
            service.get(uuid4())


# ---------------------------------------------------------------------------
# List (filter pass-through)
# ---------------------------------------------------------------------------


class TestFollowUpServiceList:
    def test_delegates_all_filters_to_repository(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        application_id = uuid4()
        recruiter_id = uuid4()
        interview_id = uuid4()
        mock_repo.list_paginated.return_value = ([], 0)

        service.list(
            application_id=application_id,
            recruiter_id=recruiter_id,
            interview_id=interview_id,
            status=FollowUpStatus.PENDING,
            priority=FollowUpPriority.HIGH,
            followup_type=FollowUpType.EMAIL,
            skip=5,
            limit=10,
        )

        mock_repo.list_paginated.assert_called_once_with(
            application_id=application_id,
            recruiter_id=recruiter_id,
            interview_id=interview_id,
            status=FollowUpStatus.PENDING,
            priority=FollowUpPriority.HIGH,
            followup_type=FollowUpType.EMAIL,
            overdue=False,
            due_today=False,
            due_this_week=False,
            skip=5,
            limit=10,
        )

    def test_passes_overdue_flag(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.list_paginated.return_value = ([], 0)
        service.list(overdue=True)
        assert mock_repo.list_paginated.call_args.kwargs["overdue"] is True

    def test_passes_due_today_flag(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.list_paginated.return_value = ([], 0)
        service.list(due_today=True)
        assert mock_repo.list_paginated.call_args.kwargs["due_today"] is True

    def test_passes_due_this_week_flag(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.list_paginated.return_value = ([], 0)
        service.list(due_this_week=True)
        assert mock_repo.list_paginated.call_args.kwargs["due_this_week"] is True

    def test_returns_items_and_total(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        followups = [_make_followup(), _make_followup()]
        mock_repo.list_paginated.return_value = (followups, 2)

        items, total = service.list()

        assert items is followups
        assert total == 2


# ---------------------------------------------------------------------------
# Update — FK validation + automatic completed_at behaviour
# ---------------------------------------------------------------------------


class TestFollowUpServiceUpdate:
    def test_updates_single_field_leaves_others_unchanged(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        followup = _make_followup()
        updated = _make_followup(id=followup.id, priority=FollowUpPriority.HIGH.value)
        mock_repo.get_or_raise.return_value = followup
        mock_repo.update.return_value = updated

        result = service.update(
            followup.id, FollowUpUpdate(priority=FollowUpPriority.HIGH)
        )

        mock_application_repo.get_or_raise.assert_not_called()
        mock_repo.update.assert_called_once_with(
            followup, {"priority": FollowUpPriority.HIGH}
        )
        assert result is updated

    def test_validates_new_application(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        followup = _make_followup()
        new_application_id = uuid4()
        mock_repo.get_or_raise.return_value = followup
        mock_application_repo.get_or_raise.return_value = MagicMock()
        mock_repo.update.return_value = followup

        service.update(
            followup.id, FollowUpUpdate(application_id=new_application_id)
        )

        mock_application_repo.get_or_raise.assert_called_once_with(new_application_id)

    def test_validates_new_recruiter(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        followup = _make_followup()
        new_recruiter_id = uuid4()
        mock_repo.get_or_raise.return_value = followup
        mock_recruiter_repo.get_or_raise.return_value = MagicMock()
        mock_repo.update.return_value = followup

        service.update(followup.id, FollowUpUpdate(recruiter_id=new_recruiter_id))

        mock_recruiter_repo.get_or_raise.assert_called_once_with(new_recruiter_id)

    def test_validates_new_interview(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_interview_repo: MagicMock,
    ) -> None:
        followup = _make_followup()
        new_interview_id = uuid4()
        mock_repo.get_or_raise.return_value = followup
        mock_interview_repo.get_or_raise.return_value = MagicMock()
        mock_repo.update.return_value = followup

        service.update(followup.id, FollowUpUpdate(interview_id=new_interview_id))

        mock_interview_repo.get_or_raise.assert_called_once_with(new_interview_id)

    def test_allows_detaching_recruiter_with_null(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_recruiter_repo: MagicMock,
    ) -> None:
        followup = _make_followup(recruiter_id=uuid4())
        mock_repo.get_or_raise.return_value = followup
        mock_repo.update.return_value = followup

        service.update(followup.id, FollowUpUpdate(recruiter_id=None))

        mock_recruiter_repo.get_or_raise.assert_not_called()

    def test_status_to_completed_sets_completed_at(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        followup = _make_followup(status=FollowUpStatus.PENDING.value, completed_at=None)
        mock_repo.get_or_raise.return_value = followup
        mock_repo.update.return_value = followup

        service.update(followup.id, FollowUpUpdate(status=FollowUpStatus.COMPLETED))

        passed = mock_repo.update.call_args[0][1]
        assert passed["completed_at"] is not None

    def test_status_to_pending_clears_completed_at(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        followup = _make_followup(
            status=FollowUpStatus.COMPLETED.value, completed_at=_STAMP
        )
        mock_repo.get_or_raise.return_value = followup
        mock_repo.update.return_value = followup

        service.update(followup.id, FollowUpUpdate(status=FollowUpStatus.PENDING))

        passed = mock_repo.update.call_args[0][1]
        assert passed["completed_at"] is None

    def test_recompleting_does_not_overwrite_existing_completed_at(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        # Already completed with a stamp; patching status=completed again must
        # not touch completed_at.
        followup = _make_followup(
            status=FollowUpStatus.COMPLETED.value, completed_at=_STAMP
        )
        mock_repo.get_or_raise.return_value = followup
        mock_repo.update.return_value = followup

        service.update(followup.id, FollowUpUpdate(status=FollowUpStatus.COMPLETED))

        passed = mock_repo.update.call_args[0][1]
        assert "completed_at" not in passed

    def test_explicit_completed_at_wins_over_auto_behaviour(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        followup = _make_followup(status=FollowUpStatus.PENDING.value, completed_at=None)
        mock_repo.get_or_raise.return_value = followup
        mock_repo.update.return_value = followup

        service.update(
            followup.id,
            FollowUpUpdate(status=FollowUpStatus.COMPLETED, completed_at=_STAMP),
        )

        passed = mock_repo.update.call_args[0][1]
        assert passed["completed_at"] == _STAMP

    def test_status_to_skipped_leaves_completed_at_untouched(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        followup = _make_followup(status=FollowUpStatus.PENDING.value, completed_at=None)
        mock_repo.get_or_raise.return_value = followup
        mock_repo.update.return_value = followup

        service.update(followup.id, FollowUpUpdate(status=FollowUpStatus.SKIPPED))

        passed = mock_repo.update.call_args[0][1]
        assert "completed_at" not in passed

    def test_raises_not_found_when_new_application_missing(
        self,
        service: FollowUpService,
        mock_repo: MagicMock,
        mock_application_repo: MagicMock,
    ) -> None:
        followup = _make_followup()
        mock_repo.get_or_raise.return_value = followup
        mock_application_repo.get_or_raise.side_effect = NotFoundError(
            "JobApplication", uuid4()
        )

        with pytest.raises(NotFoundError):
            service.update(followup.id, FollowUpUpdate(application_id=uuid4()))

    def test_propagates_not_found_when_followup_missing(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("FollowUp", uuid4())

        with pytest.raises(NotFoundError):
            service.update(uuid4(), FollowUpUpdate(title="New title"))


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestFollowUpServiceDelete:
    def test_deletes_existing_followup(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        followup = _make_followup()
        mock_repo.get_or_raise.return_value = followup

        service.delete(followup.id)

        mock_repo.delete.assert_called_once_with(followup)

    def test_propagates_not_found_from_repository(
        self, service: FollowUpService, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_or_raise.side_effect = NotFoundError("FollowUp", uuid4())

        with pytest.raises(NotFoundError):
            service.delete(uuid4())
