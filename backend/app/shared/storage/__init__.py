from functools import lru_cache

from app.core.config import settings
from app.shared.storage.base import (
    FileNotFoundInStorageError,
    FileStorage,
    StorageError,
)
from app.shared.storage.local import LocalFileStorage

__all__ = [
    "FileStorage",
    "StorageError",
    "FileNotFoundInStorageError",
    "get_storage",
]


@lru_cache
def get_storage() -> FileStorage:
    """
    Return the configured storage backend.

    This factory is the single seam where the storage implementation is chosen.
    Adding cloud storage later means writing an AzureBlobStorage / S3Storage /
    GoogleDriveStorage class against FileStorage and adding a branch here — no
    other code changes, because every caller depends only on the interface.
    """
    backend = settings.STORAGE_BACKEND
    if backend == "local":
        return LocalFileStorage(settings.STORAGE_LOCAL_PATH)
    raise ValueError(f"Unsupported STORAGE_BACKEND: {backend!r}")
