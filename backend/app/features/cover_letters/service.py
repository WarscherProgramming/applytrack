from sqlalchemy.orm import Session

from app.features.cover_letters.repository import CoverLetterRepository
from app.shared.documents.service import DocumentService


class CoverLetterService(DocumentService):
    def __init__(self, db: Session) -> None:
        super().__init__(
            repository=CoverLetterRepository(db),
            storage_prefix="cover_letters",
            resource_name="Cover letter",
        )
