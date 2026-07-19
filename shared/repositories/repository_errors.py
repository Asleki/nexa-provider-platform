"""
============================================================
Nexa Provider Platform
File: shared/repositories/repository_errors.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Defines the exception hierarchy used by the Shared Repository
Foundation.

Repository exceptions isolate higher layers from storage,
filesystem and backend-specific failures while preserving
structured operational context for logging, testing and future
audit integration.
"""

from __future__ import annotations

from typing import Any

from .repository_types import RepositoryOperation


REPOSITORY_ERROR_PREFIX = "NPP-REPOSITORY"


def _normalize_operation(
    operation: RepositoryOperation | str | None,
) -> str | None:
    """Normalize a repository operation into a string value."""

    if operation is None:
        return None

    if isinstance(operation, RepositoryOperation):
        return operation.value

    normalized = str(operation).strip()
    return normalized or None


class RepositoryError(RuntimeError):
    """
    Base exception for repository-layer failures.

    Parameters
    ----------
    message:
        Human-readable error description.

    operation:
        Repository operation being performed.

    repository:
        Logical repository name.

    record_id:
        Identifier of the affected record, when applicable.

    repository_type:
        Repository implementation type, such as ``local``.

    cause:
        Original exception or implementation-specific cause.

    metadata:
        Additional implementation-neutral diagnostic context.
    """

    error_code = f"{REPOSITORY_ERROR_PREFIX}-001"

    def __init__(
        self,
        message: str,
        *,
        operation: RepositoryOperation | str | None = None,
        repository: str | None = None,
        record_id: str | None = None,
        repository_type: str | None = None,
        cause: BaseException | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        normalized_message = str(message).strip()

        if not normalized_message:
            normalized_message = self.__class__.__name__

        super().__init__(normalized_message)

        self.message = normalized_message
        self.operation = _normalize_operation(operation)
        self.repository = (
            repository.strip()
            if isinstance(repository, str) and repository.strip()
            else None
        )
        self.record_id = (
            record_id.strip()
            if isinstance(record_id, str) and record_id.strip()
            else None
        )
        self.repository_type = (
            repository_type.strip()
            if (
                isinstance(repository_type, str)
                and repository_type.strip()
            )
            else None
        )
        self.cause = cause
        self.metadata = dict(metadata or {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize the repository error into a dictionary."""

        return {
            "error": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "operation": self.operation,
            "repository": self.repository,
            "record_id": self.record_id,
            "repository_type": self.repository_type,
            "cause": (
                self.cause.__class__.__name__
                if self.cause is not None
                else None
            ),
            "metadata": dict(self.metadata),
        }


class RepositoryConfigurationError(RepositoryError, ValueError):
    """Raised when repository configuration is invalid."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-002"


class RepositoryInitializationError(RepositoryError):
    """Raised when a repository cannot be initialized."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-003"


class RepositoryOperationError(RepositoryError):
    """Base exception for repository operation failures."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-010"


class RepositoryCreateError(RepositoryOperationError):
    """Raised when a repository record cannot be created."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-011"


class RepositoryReadError(RepositoryOperationError):
    """Raised when a repository record cannot be read."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-012"


class RepositoryUpdateError(RepositoryOperationError):
    """Raised when a repository record cannot be updated."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-013"


class RepositoryDeleteError(RepositoryOperationError):
    """Raised when a repository record cannot be deleted."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-014"


class RepositoryListError(RepositoryOperationError):
    """Raised when repository records cannot be listed."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-015"


class RepositoryExistsError(RepositoryOperationError):
    """Raised when repository existence cannot be checked."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-016"


class RepositoryCountError(RepositoryOperationError):
    """Raised when repository records cannot be counted."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-017"


class RepositoryRecordError(RepositoryError):
    """Base exception for repository record failures."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-020"


class RepositoryRecordNotFoundError(
    RepositoryRecordError,
    LookupError,
):
    """Raised when a requested repository record does not exist."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-021"


class RepositoryDuplicateRecordError(
    RepositoryRecordError,
    ValueError,
):
    """Raised when a repository record already exists."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-022"


class RepositoryInvalidRecordError(
    RepositoryRecordError,
    ValueError,
):
    """Raised when a repository record is invalid."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-023"


class RepositoryIdentifierError(
    RepositoryRecordError,
    ValueError,
):
    """Raised when a repository identifier is invalid."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-024"


class RepositoryImmutableIdentifierError(
    RepositoryIdentifierError,
):
    """Raised when an immutable record identifier is changed."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-025"


class RepositoryRegistrationError(RepositoryError):
    """Raised when repository registration fails."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-030"


class RepositoryAlreadyRegisteredError(
    RepositoryRegistrationError,
    ValueError,
):
    """Raised when a repository type is already registered."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-031"


class RepositoryNotRegisteredError(
    RepositoryRegistrationError,
    LookupError,
):
    """Raised when a repository type is not registered."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-032"


class RepositoryFactoryError(RepositoryError):
    """Raised when repository construction fails."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-040"


class RepositoryUnsupportedOperationError(
    RepositoryOperationError,
    NotImplementedError,
):
    """Raised when a repository operation is unsupported."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-050"


class RepositoryStorageError(RepositoryOperationError):
    """
    Raised when a storage-layer failure reaches the repository boundary.

    The repository layer should wrap storage exceptions with this error
    or one of the operation-specific repository exceptions so higher
    layers do not depend on storage exception types.
    """

    error_code = f"{REPOSITORY_ERROR_PREFIX}-060"


class RepositoryDataCorruptionError(RepositoryStorageError):
    """Raised when persisted repository data is malformed or inconsistent."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-061"


class RepositorySchemaError(RepositoryStorageError, ValueError):
    """Raised when persisted repository data violates its schema."""

    error_code = f"{REPOSITORY_ERROR_PREFIX}-062"


__all__ = [
    "REPOSITORY_ERROR_PREFIX",
    "RepositoryAlreadyRegisteredError",
    "RepositoryConfigurationError",
    "RepositoryCountError",
    "RepositoryCreateError",
    "RepositoryDataCorruptionError",
    "RepositoryDeleteError",
    "RepositoryDuplicateRecordError",
    "RepositoryError",
    "RepositoryExistsError",
    "RepositoryFactoryError",
    "RepositoryIdentifierError",
    "RepositoryImmutableIdentifierError",
    "RepositoryInitializationError",
    "RepositoryInvalidRecordError",
    "RepositoryListError",
    "RepositoryNotRegisteredError",
    "RepositoryOperationError",
    "RepositoryReadError",
    "RepositoryRecordError",
    "RepositoryRecordNotFoundError",
    "RepositoryRegistrationError",
    "RepositorySchemaError",
    "RepositoryStorageError",
    "RepositoryUnsupportedOperationError",
    "RepositoryUpdateError",
]
