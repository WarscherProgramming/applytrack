import logging
from pathlib import Path

from app.shared.storage.base import FileNotFoundInStorageError, FileStorage, StorageError

logger = logging.getLogger(__name__)


class LocalFileStorage(FileStorage):
    """
    Filesystem-backed implementation of FileStorage.

    Files are written under a single configurable base directory. Keys are
    treated as relative paths beneath that root; any key that resolves outside
    the root (e.g. via "../") is rejected, so a malicious or buggy key can never
    read or clobber arbitrary files on the host.
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()
        # Create the root eagerly so the first upload never races a missing dir.
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Normalise and confine the key to base_path. relative_to() raises if the
        # resolved path escapes the root, which we translate into a StorageError.
        candidate = (self.base_path / key).resolve()
        try:
            candidate.relative_to(self.base_path)
        except ValueError as exc:
            raise StorageError(f"Illegal storage key '{key}'") from exc
        return candidate

    def save(self, key: str, data: bytes) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.debug("Stored file key=%s bytes=%d", key, len(data))

    def load(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.is_file():
            raise FileNotFoundInStorageError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        # missing_ok keeps delete idempotent — deleting a record whose file was
        # already removed must not error.
        path.unlink(missing_ok=True)
        logger.debug("Deleted file key=%s", key)

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()
