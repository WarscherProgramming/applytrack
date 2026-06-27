from sqlalchemy.orm import Session

from app.features.resumes.repository import ResumeRepository
from app.shared.documents.service import DocumentService


class ResumeService(DocumentService):
    def __init__(self, db: Session) -> None:
        super().__init__(
            repository=ResumeRepository(db),
            storage_prefix="resumes",
            resource_name="Resume",
        )
