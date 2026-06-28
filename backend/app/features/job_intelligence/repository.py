from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.model import Resume


class JobIntelligenceRepository:
    """Read-only data access for Job Intelligence."""

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def list_resume_match_analyses(self) -> list[ResumeMatchAnalysis]:
        return list(
            self.db.scalars(
                select(ResumeMatchAnalysis).order_by(ResumeMatchAnalysis.created_at.asc())
                .where(ResumeMatchAnalysis.user_id == self.user_id)
            ).all()
        )

    def list_interview_prep_packages(self) -> list[InterviewPrepPackage]:
        return list(
            self.db.scalars(
                select(InterviewPrepPackage).order_by(InterviewPrepPackage.created_at.asc())
                .where(InterviewPrepPackage.user_id == self.user_id)
            ).all()
        )

    def list_applications(self) -> list[JobApplication]:
        return list(
            self.db.scalars(
                select(JobApplication).where(JobApplication.user_id == self.user_id)
            ).all()
        )

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company).where(Company.user_id == self.user_id)).all())

    def list_resumes(self) -> list[Resume]:
        return list(self.db.scalars(select(Resume).where(Resume.user_id == self.user_id)).all())

