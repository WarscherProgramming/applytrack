from sqlalchemy.orm import Session
from uuid import UUID

from app.features.resumes.repository import ResumeRepository
from app.shared.documents.service import DocumentService


class ResumeService(DocumentService):
    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(
            repository=ResumeRepository(db),
            storage_prefix="resumes",
            resource_name="Resume",
            user_id=user_id,
        )
