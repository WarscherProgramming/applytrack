from abc import ABC, abstractmethod


class StorageError(Exception):
    """Raised when a storage backend cannot complete an operation."""


class FileNotFoundInStorageError(StorageError):
    """Raised when a requested key does not exist in the backend."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"No stored file for key '{key}'")


class FileStorage(ABC):
    """
    Backend-agnostic blob storage interface.

    The entire application talks to files exclusively through this interface.
    A "key" is an opaque, backend-relative path (e.g. "resumes/<uuid>.pdf") that
    the caller persists in the database; the caller never knows whether the bytes
    live on a local disk, in Azure Blob, S3, or Google Drive.

    Swapping local storage for a cloud backend is therefore a single change in
    the factory (see get_storage) — no service, router, or model changes. Service
    code generates keys and hands bytes to save(); it has no filesystem knowledge.
    """

    @abstractmethod
    def save(self, key: str, data: bytes) -> None:
        """Persist `data` under `key`, overwriting any existing object."""

    @abstractmethod
    def load(self, key: str) -> bytes:
        """Return the bytes stored under `key`.

        Raises FileNotFoundInStorageError if the key does not exist.
        """

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the object at `key`. A missing key is a no-op (idempotent)."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """True if an object is stored under `key`."""
