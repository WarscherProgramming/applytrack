import mimetypes
from collections.abc import Callable
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi import status as http_status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.shared.documents.schema import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
)
from app.shared.documents.service import DocumentService

# A service factory takes a request-scoped Session and returns the concrete
# (Resume / CoverLetter) service.
ServiceFactory = Callable[[Session], DocumentService]


def build_document_router(
    *,
    prefix: str,
    tag: str,
    service_factory: ServiceFactory,
    upload_field_label: str,
) -> APIRouter:
    """
    Build a full CRUD + upload/download router for a document resource.

    Resumes and cover letters expose byte-for-byte identical REST surfaces, so
    the routes are generated once here. Each feature module calls this with its
    own service factory and URL prefix.
    """
    router = APIRouter(prefix=prefix, tags=[tag])

    def _get_service(db: Annotated[Session, Depends(get_db)]) -> DocumentService:
        return service_factory(db)

    ServiceDep = Annotated[DocumentService, Depends(_get_service)]

    @router.post(
        "/",
        response_model=DocumentResponse,
        status_code=http_status.HTTP_201_CREATED,
        summary=f"Upload a {upload_field_label}",
    )
    async def upload_document(
        service: ServiceDep,
        file: Annotated[UploadFile, File(description=f"The {upload_field_label} file")],
        name: Annotated[str | None, Form()] = None,
        notes: Annotated[str | None, Form()] = None,
    ) -> DocumentResponse:
        content = await file.read()
        record = service.upload(
            file_name=file.filename or "document",
            content=content,
            name=name,
            notes=notes,
        )
        return DocumentResponse.model_validate(record)

    @router.get("/", response_model=DocumentListResponse)
    def list_documents(
        service: ServiceDep,
        query: Annotated[
            str | None, Query(description="Search by document or file name")
        ] = None,
        name: Annotated[
            str | None, Query(description="Filter to a single document's versions")
        ] = None,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
    ) -> DocumentListResponse:
        items, total = service.list(query=query, name=name, skip=skip, limit=limit)
        return DocumentListResponse(items=items, total=total, skip=skip, limit=limit)

    @router.get("/{doc_id}", response_model=DocumentResponse)
    def get_document(doc_id: UUID, service: ServiceDep) -> DocumentResponse:
        return DocumentResponse.model_validate(service.get(doc_id))

    @router.get("/{doc_id}/download")
    def download_document(doc_id: UUID, service: ServiceDep) -> Response:
        downloaded = service.download(doc_id)
        file_name = downloaded.record.file_name
        media_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        # RFC 5987 filename* handles non-ASCII names; the plain filename is a
        # best-effort fallback for older clients.
        disposition = (
            f"attachment; filename=\"{file_name}\"; "
            f"filename*=UTF-8''{quote(file_name)}"
        )
        return Response(
            content=downloaded.content,
            media_type=media_type,
            headers={"Content-Disposition": disposition},
        )

    @router.patch("/{doc_id}", response_model=DocumentResponse)
    def update_document(
        doc_id: UUID, data: DocumentUpdate, service: ServiceDep
    ) -> DocumentResponse:
        return DocumentResponse.model_validate(service.update(doc_id, data))

    @router.delete("/{doc_id}", status_code=http_status.HTTP_204_NO_CONTENT)
    def delete_document(doc_id: UUID, service: ServiceDep) -> None:
        service.delete(doc_id)

    return router
