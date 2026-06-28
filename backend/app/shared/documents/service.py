import logging
import uuid
from pathlib import PurePosixPath
from uuid import UUID

from app.core.config import settings
from app.exceptions.http import ValidationError
from app.shared.documents.model import DocumentBase
from app.shared.documents.repository import DocumentRepository
from app.shared.documents.schema import DocumentUpdate
from app.shared.storage import FileNotFoundInStorageError, get_storage

logger = logging.getLogger(__name__)

# Document formats a job seeker realistically uploads. Stored lowercase, with the
# leading dot. Enforced in the service (not the DB) so the list can change freely.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"}
)


class DownloadedDocument:
    """A document's metadata paired with its bytes, returned to the router."""

    def __init__(self, record: DocumentBase, content: bytes) -> None:
        self.record = record
        self.content = content


class DocumentService:
    """
    Shared upload / download / CRUD logic for versioned documents.

    Subclasses (ResumeService, CoverLetterService) only supply the concrete
    repository, the storage-key prefix, and a human resource name for errors.
    All filesystem access goes through the FileStorage abstraction — this class
    never imports a storage backend, so cloud storage drops in unchanged.
    """

    def __init__(
        self,
        *,
        repository: DocumentRepository,
        storage_prefix: str,
        resource_name: str,
        user_id: UUID,
    ) -> None:
        self.user_id = user_id
        self.repo = repository
        self.storage = get_storage()
        self.storage_prefix = storage_prefix
        self.resource_name = resource_name

    # -- helpers ------------------------------------------------------------

    def _validate(self, file_name: str, content: bytes) -> str:
        """Validate the upload and return its normalised extension (".pdf")."""
        ext = PurePosixPath(file_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ValidationError(
                f"Unsupported file type '{ext or file_name}'. Allowed: {allowed}"
            )
        if not content:
            raise ValidationError("Uploaded file is empty")
        if len(content) > settings.STORAGE_MAX_UPLOAD_BYTES:
            mb = settings.STORAGE_MAX_UPLOAD_BYTES / (1024 * 1024)
            raise ValidationError(f"File exceeds the {mb:.0f} MB upload limit")
        return ext

    # -- operations ---------------------------------------------------------

    def upload(
        self,
        *,
        file_name: str,
        content: bytes,
        name: str | None = None,
        notes: str | None = None,
    ) -> DocumentBase:
        ext = self._validate(file_name, content)

        # Generate the id up front so the storage key is deterministic and unique
        # regardless of (re-used) file names; the key never leaks the original
        # name, avoiding collisions and path-injection from user input.
        doc_id = uuid.uuid4()
        key = f"{self.storage_prefix}/{doc_id}{ext}"

        display_name = (name or "").strip() or PurePosixPath(file_name).stem
        display_name = display_name or file_name
        version = self.repo.next_version(display_name, self.user_id)

        # Insert the row first (flush only — get_db owns the commit). If the
        # subsequent storage write fails, the raised error rolls the row back, so
        # we never persist a record pointing at a missing file.
        record = self.repo.create(
            {
                "id": doc_id,
                "name": display_name,
                "file_name": file_name,
                "storage_path": key,
                "version": version,
                "notes": (notes or None),
                "user_id": self.user_id,
            }
        )
        self.storage.save(key, content)

        logger.info(
            "Uploaded %s id=%s name=%r version=%d bytes=%d",
            self.resource_name,
            record.id,
            display_name,
            version,
            len(content),
        )
        return record

    def get(self, doc_id: UUID) -> DocumentBase:
        return self.repo.get_or_raise_for_user(doc_id, self.user_id)

    def list(
        self,
        *,
        query: str | None = None,
        name: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DocumentBase], int]:
        return self.repo.list_paginated(
            query=query,
            name=name,
            user_id=self.user_id,
            skip=skip,
            limit=limit,
        )

    def download(self, doc_id: UUID) -> DownloadedDocument:
        record = self.repo.get_or_raise_for_user(doc_id, self.user_id)
        try:
            content = self.storage.load(record.storage_path)
        except FileNotFoundInStorageError as exc:
            # Row exists but the blob is gone (e.g. manual deletion). Surface a
            # clean 404 rather than a 500.
            from app.exceptions.http import NotFoundError

            raise NotFoundError(
                f"{self.resource_name} file", record.storage_path
            ) from exc
        return DownloadedDocument(record, content)

    def update(self, doc_id: UUID, data: DocumentUpdate) -> DocumentBase:
        record = self.repo.get_or_raise_for_user(doc_id, self.user_id)
        updates = data.model_dump(exclude_unset=True)
        updated = self.repo.update(record, updates)
        logger.info(
            "Updated %s id=%s fields=%s",
            self.resource_name,
            doc_id,
            list(updates.keys()),
        )
        return updated

    def delete(self, doc_id: UUID) -> None:
        record = self.repo.get_or_raise_for_user(doc_id, self.user_id)
        key = record.storage_path
        self.repo.delete(record)
        # Remove the blob after the row delete is staged. delete() is idempotent,
        # so a missing blob is harmless.
        self.storage.delete(key)
        logger.info("Deleted %s id=%s", self.resource_name, doc_id)
