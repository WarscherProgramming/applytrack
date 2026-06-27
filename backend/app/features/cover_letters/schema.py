"""Cover-letter schemas.

Cover letters share the generic document contract, so the shared schemas are
re-exported under cover-letter-specific names for a stable import path.
"""

from app.shared.documents.schema import (
    DocumentListResponse as CoverLetterListResponse,
)
from app.shared.documents.schema import (
    DocumentResponse as CoverLetterResponse,
)
from app.shared.documents.schema import (
    DocumentUpdate as CoverLetterUpdate,
)

__all__ = [
    "CoverLetterResponse",
    "CoverLetterUpdate",
    "CoverLetterListResponse",
]
