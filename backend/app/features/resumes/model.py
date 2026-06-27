from app.shared.documents.model import DocumentBase


class Resume(DocumentBase):
    """A single uploaded resume version. Columns come from DocumentBase."""

    __tablename__ = "resumes"
