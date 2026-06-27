from sqlalchemy.orm import Session

from app.features.resumes.model import Resume
from app.shared.documents.repository import DocumentRepository


class ResumeRepository(DocumentRepository[Resume]):
    def __init__(self, db: Session) -> None:
        super().__init__(Resume, db)
