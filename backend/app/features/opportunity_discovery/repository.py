from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.features.applications.model import JobApplication
from app.features.applications.repository import ApplicationRepository
from app.features.companies.model import Company
from app.features.companies.repository import CompanyRepository
from app.features.cover_letters.model import CoverLetter
from app.features.cover_letters.repository import CoverLetterRepository
from app.features.resumes.model import Resume
from app.features.resumes.repository import ResumeRepository


class OpportunityDiscoveryRepository:
    """Data access for opportunity discovery.

    Discovery results are external/read-only. Persistence is limited to creating
    companies and draft applications when the user explicitly saves a posting.
    """

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id
        self.companies = CompanyRepository(db)
        self.applications = ApplicationRepository(db)
        self.resumes = ResumeRepository(db)
        self.cover_letters = CoverLetterRepository(db)

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

    def list_cover_letters(self) -> list[CoverLetter]:
        return list(
            self.db.scalars(
                select(CoverLetter).where(CoverLetter.user_id == self.user_id)
            ).all()
        )

    def get_resume(self, resume_id):
        return self.resumes.get_or_raise_for_user(resume_id, self.user_id)

    def get_cover_letter(self, cover_letter_id):
        return self.cover_letters.get_or_raise_for_user(cover_letter_id, self.user_id)

    def get_company_by_name(self, name: str) -> Company | None:
        return self.companies.get_by_name(name, self.user_id)

    def create_company(self, data: dict) -> Company:
        return self.companies.create(data | {"user_id": self.user_id})

    def create_application(self, data: dict) -> JobApplication:
        return self.applications.create(data | {"user_id": self.user_id})
