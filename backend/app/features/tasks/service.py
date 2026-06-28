from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.features.applications.repository import ApplicationRepository
from app.features.companies.repository import CompanyRepository
from app.features.daily_briefing.model import NotificationPriority
from app.features.daily_briefing.service import DailyBriefingService
from app.features.followups.model import FollowUp
from app.features.followups.repository import FollowUpRepository
from app.features.gmail.models import EmailMessage
from app.features.interviews.model import Interview
from app.features.interviews.repository import InterviewRepository
from app.features.recruiters.repository import RecruiterRepository
from app.features.tasks.model import Task, TaskPriority, TaskSource, TaskStatus
from app.features.tasks.repository import TaskRepository
from app.features.tasks.schemas import (
    TaskCreate,
    TaskGenerationResponse,
    TaskResponse,
    TaskUpdate,
)

PRIORITY_MAP = {
    NotificationPriority.LOW: TaskPriority.LOW,
    NotificationPriority.MEDIUM: TaskPriority.MEDIUM,
    NotificationPriority.HIGH: TaskPriority.HIGH,
    NotificationPriority.URGENT: TaskPriority.URGENT,
}


class TaskService:
    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id
        self.repo = TaskRepository(db)
        self.application_repo = ApplicationRepository(db)
        self.company_repo = CompanyRepository(db)
        self.recruiter_repo = RecruiterRepository(db)
        self.interview_repo = InterviewRepository(db)
        self.followup_repo = FollowUpRepository(db)

    def create(self, data: TaskCreate) -> Task:
        payload = data.model_dump()
        self._validate_links(payload)
        if payload["status"] == TaskStatus.COMPLETED and payload["completed_at"] is None:
            payload["completed_at"] = datetime.now(UTC)
        return self.repo.create(_enum_values(payload) | {"user_id": self.user_id})

    def get(self, task_id: UUID) -> Task:
        return self.repo.get_or_raise_for_user(task_id, self.user_id)

    def list(
        self,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        source: TaskSource | None = None,
        application_id: UUID | None = None,
        company_id: UUID | None = None,
        recruiter_id: UUID | None = None,
        interview_id: UUID | None = None,
        followup_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        return self.repo.list_paginated(
            status=status,
            priority=priority,
            source=source,
            application_id=application_id,
            company_id=company_id,
            recruiter_id=recruiter_id,
            interview_id=interview_id,
            followup_id=followup_id,
            user_id=self.user_id,
            skip=skip,
            limit=limit,
        )

    def update(self, task_id: UUID, data: TaskUpdate) -> Task:
        task = self.repo.get_or_raise_for_user(task_id, self.user_id)
        updates = data.model_dump(exclude_unset=True)
        self._validate_links(updates)
        if "status" in updates:
            if updates["status"] == TaskStatus.COMPLETED:
                if "completed_at" not in updates and task.completed_at is None:
                    updates["completed_at"] = datetime.now(UTC)
            elif updates["status"] in {
                TaskStatus.BACKLOG,
                TaskStatus.TODAY,
                TaskStatus.IN_PROGRESS,
            }:
                if "completed_at" not in updates:
                    updates["completed_at"] = None
        return self.repo.update(task, _enum_values(updates))

    def complete(self, task_id: UUID) -> Task:
        task = self.repo.get_or_raise_for_user(task_id, self.user_id)
        return self.repo.update(
            task,
            {
                "status": TaskStatus.COMPLETED.value,
                "completed_at": datetime.now(UTC),
            },
        )

    def dismiss(self, task_id: UUID) -> Task:
        task = self.repo.get_or_raise_for_user(task_id, self.user_id)
        return self.repo.update(task, {"status": TaskStatus.DISMISSED.value})

    def delete(self, task_id: UUID) -> None:
        task = self.repo.get_or_raise_for_user(task_id, self.user_id)
        self.repo.delete(task)

    def generate_from_daily_briefing(self) -> TaskGenerationResponse:
        briefing = DailyBriefingService(self.db, self.user_id).build_briefing()
        response = TaskGenerationResponse()
        for item in briefing.prioritized_actions:
            due_date = item.due_at.date() if item.due_at else briefing.briefing_date
            self._upsert_generated(
                response,
                {
                    "title": item.title,
                    "description": item.detail,
                    "status": TaskStatus.TODAY,
                    "priority": PRIORITY_MAP.get(item.priority, TaskPriority.MEDIUM),
                    "due_date": due_date,
                    "source": TaskSource.DAILY_BRIEFING,
                    "source_key": f"daily_briefing:{briefing.briefing_date}:{item.id}",
                },
            )
        for recommendation in briefing.ai_recommendations:
            self._upsert_generated(
                response,
                {
                    "title": recommendation[:255],
                    "description": "Generated from Daily Briefing AI recommendations.",
                    "status": TaskStatus.TODAY,
                    "priority": TaskPriority.MEDIUM,
                    "due_date": briefing.briefing_date,
                    "source": TaskSource.AI_RECOMMENDATION,
                    "source_key": (
                        f"daily_ai:{briefing.briefing_date}:"
                        f"{_stable_hash(recommendation)}"
                    ),
                },
            )
        return response

    def generate_from_overdue_followups(self) -> TaskGenerationResponse:
        today = date.today()
        response = TaskGenerationResponse()
        for followup in self.repo.list_overdue_followups(today, self.user_id):
            self._upsert_generated(response, self._followup_task(followup))
        return response

    def generate_from_upcoming_interviews(self) -> TaskGenerationResponse:
        now = datetime.now(UTC)
        response = TaskGenerationResponse()
        for interview in self.repo.list_upcoming_interviews(
            now=now,
            until=now + timedelta(days=7),
            user_id=self.user_id,
        ):
            self._upsert_generated(response, self._interview_task(interview))
        return response

    def generate_from_recruiter_emails(self) -> TaskGenerationResponse:
        response = TaskGenerationResponse()
        for email in self.repo.list_unread_recruiter_emails(self.user_id):
            if _looks_recruiting_related(email):
                self._upsert_generated(response, self._email_task(email))
        return response

    def generate_all(self) -> TaskGenerationResponse:
        combined = TaskGenerationResponse()
        for response in (
            self.generate_from_daily_briefing(),
            self.generate_from_overdue_followups(),
            self.generate_from_upcoming_interviews(),
            self.generate_from_recruiter_emails(),
        ):
            combined.created += response.created
            combined.updated += response.updated
            combined.skipped += response.skipped
            combined.items.extend(response.items)
        return combined

    def _upsert_generated(
        self, response: TaskGenerationResponse, payload: dict
    ) -> Task:
        source_key = payload["source_key"]
        existing = self.repo.get_by_source_key(source_key, self.user_id)
        data = _enum_values(payload) | {"user_id": self.user_id}
        if existing is None:
            task = self.repo.create(data)
            response.created += 1
            response.items.append(TaskResponse.model_validate(task))
            return task
        if existing.status in {TaskStatus.COMPLETED.value, TaskStatus.DISMISSED.value}:
            response.skipped += 1
            response.items.append(TaskResponse.model_validate(existing))
            return existing
        task = self.repo.update(existing, data)
        response.updated += 1
        response.items.append(TaskResponse.model_validate(task))
        return task

    def _followup_task(self, followup: FollowUp) -> dict:
        return {
            "title": f"Follow up: {followup.title}",
            "description": followup.description or "Overdue follow-up reminder.",
            "status": TaskStatus.TODAY,
            "priority": TaskPriority(followup.priority),
            "due_date": followup.due_date,
            "source": TaskSource.FOLLOWUP,
            "application_id": followup.application_id,
            "recruiter_id": followup.recruiter_id,
            "interview_id": followup.interview_id,
            "followup_id": followup.id,
            "source_key": f"followup:{followup.id}",
        }

    def _interview_task(self, interview: Interview) -> dict:
        applications = {item.id: item for item in self.repo.list_applications(self.user_id)}
        application = applications.get(interview.application_id)
        title = (
            f"Prepare for interview: {application.job_title}"
            if application
            else "Prepare for upcoming interview"
        )
        return {
            "title": title,
            "description": interview.notes or interview.interview_type or "Upcoming interview.",
            "status": (
                TaskStatus.TODAY
                if interview.scheduled_at.date() == date.today()
                else TaskStatus.BACKLOG
            ),
            "priority": TaskPriority.HIGH,
            "due_date": interview.scheduled_at.date(),
            "source": TaskSource.INTERVIEW,
            "application_id": interview.application_id,
            "recruiter_id": interview.recruiter_id,
            "interview_id": interview.id,
            "source_key": f"interview:{interview.id}",
        }

    def _email_task(self, email: EmailMessage) -> dict:
        return {
            "title": f"Review recruiter email: {email.subject or '(no subject)'}"[:255],
            "description": (
                f"From {email.sender}. {email.body_preview or email.match_reason or ''}"
            ).strip(),
            "status": TaskStatus.TODAY,
            "priority": TaskPriority.MEDIUM,
            "due_date": date.today(),
            "source": TaskSource.GMAIL,
            "application_id": email.application_id,
            "company_id": email.company_id,
            "recruiter_id": email.recruiter_id,
            "interview_id": email.interview_id,
            "source_key": f"gmail:{email.id}",
        }

    def _validate_links(self, payload: dict) -> None:
        if payload.get("application_id") is not None:
            self.application_repo.get_or_raise_for_user(
                payload["application_id"],
                self.user_id,
            )
        if payload.get("company_id") is not None:
            self.company_repo.get_or_raise_for_user(payload["company_id"], self.user_id)
        if payload.get("recruiter_id") is not None:
            self.recruiter_repo.get_or_raise_for_user(
                payload["recruiter_id"],
                self.user_id,
            )
        if payload.get("interview_id") is not None:
            self.interview_repo.get_or_raise_for_user(
                payload["interview_id"],
                self.user_id,
            )
        if payload.get("followup_id") is not None:
            self.followup_repo.get_or_raise_for_user(
                payload["followup_id"],
                self.user_id,
            )


def _enum_values(payload: dict) -> dict:
    return {
        key: value.value if hasattr(value, "value") else value
        for key, value in payload.items()
    }


def _stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def _looks_recruiting_related(email: EmailMessage) -> bool:
    haystack = f"{email.subject or ''} {email.sender} {email.match_reason or ''}".lower()
    return any(
        token in haystack
        for token in ("recruit", "talent", "interview", "application", "hiring")
    )
