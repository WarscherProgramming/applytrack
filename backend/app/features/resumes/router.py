from app.features.resumes.service import ResumeService
from app.shared.documents.router import build_document_router

router = build_document_router(
    prefix="/resumes",
    tag="resumes",
    service_factory=ResumeService,
    upload_field_label="resume",
)
