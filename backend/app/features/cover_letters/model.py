from app.shared.documents.model import DocumentBase


class CoverLetter(DocumentBase):
    """A single uploaded cover-letter version. Columns come from DocumentBase."""

    __tablename__ = "cover_letters"
