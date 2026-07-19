"""
============================================================
Nexa Provider Platform
File: shared/storage/storage_errors.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

Purpose
-------
Defines the exception hierarchy used by the Nexa Provider
Platform Storage Foundation.

The storage layer translates low-level filesystem, serialization,
encoding, integrity, and adapter failures into clear platform
exceptions. Callers can therefore handle storage failures without
depending directly on implementation-specific Python exceptions.

Responsibilities
----------------
This module is responsible for:

- defining the base storage exception;
- classifying read, write, append, delete, and listing failures;
- representing invalid or unsafe storage paths;
- representing serialization and deserialization failures;
- representing data-integrity and concurrency failures;
- representing unsupported or unavailable storage backends;
- preserving useful operation and path context.

Non-Responsibilities
--------------------
This module does not:

- perform filesystem operations;
- serialize or deserialize records;
- select storage adapters;
- create directories;
- write logs or audit records;
- apply provider-domain business rules.
============================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


STORAGE_ERROR_PREFIX: Final[str] = "NPP storage error"


class StorageError(RuntimeError):
    """
    Base exception for all Storage Foundation failures.
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        path: str | Path | None = None,
        backend: str | None = None,
    ) -> None:
        normalized_message = str(message).strip()

        if not normalized_message:
            normalized_message = "An unspecified storage failure occurred."

        self.message = normalized_message
        self.operation = self._normalize_optional_text(operation)
        self.path = Path(path) if path is not None else None
        self.backend = self._normalize_optional_text(backend)

        super().__init__(self._build_message())

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        """Normalize optional text values."""

        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    def _build_message(self) -> str:
        """Build the final exception message with available context."""

        context: list[str] = []

        if self.operation is not None:
            context.append(f"operation={self.operation}")

        if self.backend is not None:
            context.append(f"backend={self.backend}")

        if self.path is not None:
            context.append(f"path={self.path}")

        if not context:
            return f"{STORAGE_ERROR_PREFIX}: {self.message}"

        joined_context = ", ".join(context)

        return (
            f"{STORAGE_ERROR_PREFIX}: {self.message} "
            f"({joined_context})"
        )

    def to_dict(self) -> dict[str, str | None]:
        """Return a serializable representation of the exception."""

        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "operation": self.operation,
            "backend": self.backend,
            "path": str(self.path) if self.path is not None else None,
        }


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is missing or inconsistent."""


class StorageInitializationError(StorageError):
    """Raised when the Storage Foundation cannot initialize safely."""


class StorageBackendError(StorageError):
    """Base exception for storage-backend failures."""


class StorageBackendUnavailableError(StorageBackendError):
    """Raised when a configured storage backend is unavailable."""


class UnsupportedStorageBackendError(StorageBackendError):
    """Raised when a requested storage backend is unsupported."""


class StoragePathError(StorageError, ValueError):
    """Base exception for invalid or unsafe storage paths."""


class StoragePathNotFoundError(StoragePathError, FileNotFoundError):
    """Raised when a required storage path does not exist."""


class StoragePathExistsError(StoragePathError, FileExistsError):
    """Raised when an operation requires a new path but it exists."""


class StoragePathPermissionError(StoragePathError, PermissionError):
    """Raised when access to a storage path is denied."""


class StoragePathTraversalError(StoragePathError):
    """Raised when a path attempts to escape its approved root."""


class StorageDirectoryError(StoragePathError):
    """Raised when a storage directory cannot be created or used."""


class StorageReadError(StorageError):
    """Raised when stored content cannot be read."""


class StorageWriteError(StorageError):
    """Raised when content cannot be written safely."""


class StorageAppendError(StorageWriteError):
    """Raised when content cannot be appended safely."""


class StorageDeleteError(StorageError):
    """Raised when stored content cannot be deleted."""


class StorageListError(StorageError):
    """Raised when storage paths cannot be listed."""


class StorageSerializationError(StorageError, ValueError):
    """Raised when a Python value cannot be serialized."""


class StorageDeserializationError(StorageError, ValueError):
    """Raised when stored content cannot be deserialized."""


class StorageEncodingError(StorageError, UnicodeError):
    """Raised when text encoding or decoding fails."""


class StorageIntegrityError(StorageError):
    """Raised when stored data fails an integrity requirement."""


class StorageCorruptionError(StorageIntegrityError):
    """Raised when persisted content appears malformed or corrupted."""


class StorageConflictError(StorageIntegrityError):
    """Raised when a safe write cannot proceed because state changed."""


class StorageConcurrencyError(StorageConflictError):
    """Raised when concurrent access violates storage guarantees."""


class StorageAtomicWriteError(StorageWriteError):
    """Raised when an atomic write or replacement cannot complete."""


class StorageRecordError(StorageError):
    """Base exception for record-level storage failures."""


class StorageRecordNotFoundError(StorageRecordError, LookupError):
    """Raised when a requested storage record does not exist."""


class StorageDuplicateRecordError(StorageRecordError):
    """Raised when an operation would create a duplicate record."""


class StorageValidationError(StorageRecordError, ValueError):
    """Raised when data is unsuitable for a storage operation."""


class StorageOperationNotSupportedError(StorageError, NotImplementedError):
    """Raised when an adapter does not support an operation."""


__all__ = [
    "STORAGE_ERROR_PREFIX",
    "StorageAppendError",
    "StorageAtomicWriteError",
    "StorageBackendError",
    "StorageBackendUnavailableError",
    "StorageConcurrencyError",
    "StorageConfigurationError",
    "StorageConflictError",
    "StorageCorruptionError",
    "StorageDeleteError",
    "StorageDeserializationError",
    "StorageDirectoryError",
    "StorageDuplicateRecordError",
    "StorageEncodingError",
    "StorageError",
    "StorageInitializationError",
    "StorageIntegrityError",
    "StorageListError",
    "StorageOperationNotSupportedError",
    "StoragePathError",
    "StoragePathExistsError",
    "StoragePathNotFoundError",
    "StoragePathPermissionError",
    "StoragePathTraversalError",
    "StorageReadError",
    "StorageRecordError",
    "StorageRecordNotFoundError",
    "StorageSerializationError",
    "StorageValidationError",
    "StorageWriteError",
    "UnsupportedStorageBackendError",
]
