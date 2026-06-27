from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.applications.model import JobApplication
from app.features.companies.model import Company
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.model import Resume


class JobIntelligenceRepository:
    """Read-only data access for Job Intelligence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_resume_match_analyses(self) -> list[ResumeMatchAnalysis]:
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

    def list_applications(self) -> list[JobApplication]:
        return list(self.db.scalars(select(JobApplication)).all())

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company)).all())

    def list_resumes(self) -> list[Resume]:
        return list(self.db.scalars(select(Resume)).all())

