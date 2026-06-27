from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class DocumentBase(BaseModel):
    """
    Abstract base for every stored document (resumes, cover letters).

    Resume and CoverLetter are separate tables — the spec keeps them as distinct
    feature modules — but their shape is identical, so the columns live here once
    to guarantee the two schemas never drift apart. Each concrete model only
    declares its __tablename__; id/timestamps come from BaseModel.
    """

    __abstract__ = True

    # Logical document name. Versions of the same document share a name, so this
    # is indexed: the library groups by name and computes the next version with a
    # MAX(version) WHERE name = ... lookup.
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Original client file name, preserved for display and for the download
    # Content-Disposition header.
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Opaque, backend-relative storage key (see app.shared.storage). Never a
    # host path — swapping to cloud storage leaves this column meaningful.
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    # 1-based, auto-assigned per name on upload.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
