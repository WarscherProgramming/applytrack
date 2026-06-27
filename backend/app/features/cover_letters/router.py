from app.features.cover_letters.service import CoverLetterService
from app.shared.documents.router import build_document_router

router = build_document_router(
    prefix="/cover-letters",
    tag="cover_letters",
    service_factory=CoverLetterService,
    upload_field_label="cover letter",
)
