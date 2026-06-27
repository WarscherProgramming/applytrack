"""Resume schemas.

Resumes share the generic document contract, so the shared schemas are
re-exported under resume-specific names for a stable, discoverable import path.
"""

from app.shared.documents.schema import (
    DocumentListResponse as ResumeListResponse,
)
from app.shared.documents.schema import (
    DocumentResponse as ResumeResponse,
)
from app.shared.documents.schema import (
    DocumentUpdate as ResumeUpdate,
)

__all__ = ["ResumeResponse", "ResumeUpdate", "ResumeListResponse"]
