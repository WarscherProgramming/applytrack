from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.usage_tracker import AIUsageRecord
from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.cover_letters.model import CoverLetter
from app.features.gmail.models import EmailMessage
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.interviews.model import Interview
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.model import Resume


class CareerIntelligenceRepository:
    """
    Read-only access for career intelligence.

    This feature is a derived analytics/read model, so it has no table and no
    migration. The repository only gathers existing records; all aggregation and
    interpretation live in the service.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_applications(self) -> list[JobApplication]:
        return list(
            self.db.scalars(
                select(JobApplication).order_by(
                    JobApplication.date_applied.asc(),
                    JobApplication.created_at.asc(),
                )
            ).all()
        )

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company)).all())

    def list_interviews(self) -> list[Interview]:
        return list(
            self.db.scalars(select(Interview).order_by(Interview.scheduled_at.asc())).all()
        )

    def list_emails(self) -> list[EmailMessage]:
        return list(
            self.db.scalars(select(EmailMessage).order_by(EmailMessage.sent_at.asc())).all()
        )

    def list_resumes(self) -> list[Resume]:
        return list(self.db.scalars(select(Resume)).all())

    def list_cover_letters(self) -> list[CoverLetter]:
        return list(self.db.scalars(select(CoverLetter)).all())

    def list_resume_analyses(self) -> list[ResumeMatchAnalysis]:
        return list(
            self.db.scalars(
                select(ResumeMatchAnalysis).order_by(ResumeMatchAnalysis.created_at.asc())
            ).all()
        )

    def list_interview_prep_packages(self) -> list[InterviewPrepPackage]:
        return list(
            self.db.scalars(
                select(InterviewPrepPackage).order_by(InterviewPrepPackage.created_at.asc())
            ).all()
        )

    def list_ai_usage(self) -> list[AIUsageRecord]:
        return list(
            self.db.scalars(select(AIUsageRecord).order_by(AIUsageRecord.created_at.asc())).all()
        )

