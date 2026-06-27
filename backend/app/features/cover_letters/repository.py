from sqlalchemy.orm import Session

from app.features.cover_letters.model import CoverLetter
from app.shared.documents.repository import DocumentRepository


class CoverLetterRepository(DocumentRepository[CoverLetter]):
    def __init__(self, db: Session) -> None:
        super().__init__(CoverLetter, db)
