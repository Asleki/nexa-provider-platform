"""
============================================================
Nexa Provider Platform
File: registries/ports/registry_repository_errors.py
Layer: Master Registry Foundation
Milestone: NPP-M008.4 — Registry Repository Interface
============================================================

Registry-specific repository exception hierarchy.

These exceptions prevent concrete memory, file, database, or remote
adapter failures from leaking into registry services.
============================================================
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from .registry_repository_types import RegistryRepositoryOperation


REGISTRY_REPOSITORY_ERROR_PREFIX = "NPP-REGISTRY-REPOSITORY"


def _normalize_operation(
    operation: RegistryRepositoryOperation | str | None,
) -> str | None:
    if operation is None:
        return None
    if isinstance(operation, RegistryRepositoryOperation):
        return operation.value
    normalized = str(operation).strip()
    return normalized or None


class RegistryRepositoryError(RuntimeError):
    """Base exception for registry repository failures."""

    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-001"

    def __init__(
        self,
        message: str,
        *,
        operation: RegistryRepositoryOperation | str | None = None,
        repository: str | None = None,
        registry_id: str | None = None,
        repository_type: str | None = None,
        cause: BaseException | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        normalized_message = str(message).strip() or self.__class__.__name__
        super().__init__(normalized_message)

        self.message = normalized_message
        self.operation = _normalize_operation(operation)
        self.repository = (
            repository.strip()
            if isinstance(repository, str) and repository.strip()
            else None
        )
        self.registry_id = (
            registry_id.strip()
            if isinstance(registry_id, str) and registry_id.strip()
            else None
        )
        self.repository_type = (
            repository_type.strip()
            if isinstance(repository_type, str) and repository_type.strip()
            else None
        )
        self.cause = cause
        self.metadata = MappingProxyType(dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "operation": self.operation,
            "repository": self.repository,
            "registry_id": self.registry_id,
            "repository_type": self.repository_type,
            "cause": (
                self.cause.__class__.__name__
                if self.cause is not None
                else None
            ),
            "metadata": dict(self.metadata),
        }


class RegistryRepositoryConfigurationError(
    RegistryRepositoryError,
    ValueError,
):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-002"


class RegistryRepositoryOperationError(RegistryRepositoryError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-010"


class RegistryAddError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-011"


class RegistryReadError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-012"


class RegistryReplaceError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-013"


class RegistryRemoveError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-014"


class RegistryListError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-015"


class RegistryExistsError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-016"


class RegistryCountError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-017"


class RegistryClearError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-018"


class RegistryRecordError(RegistryRepositoryError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-020"


class RegistryNotFoundError(RegistryRecordError, LookupError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-021"


class RegistryDuplicateError(RegistryRecordError, ValueError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-022"


class RegistryInvalidRecordError(RegistryRecordError, ValueError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-023"


class RegistryIdentifierError(RegistryRecordError, ValueError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-024"


class RegistryUnsupportedOperationError(
    RegistryRepositoryOperationError,
    NotImplementedError,
):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-050"


class RegistryStorageError(RegistryRepositoryOperationError):
    error_code = f"{REGISTRY_REPOSITORY_ERROR_PREFIX}-060"


__all__ = [
    "REGISTRY_REPOSITORY_ERROR_PREFIX",
    "RegistryAddError",
    "RegistryClearError",
    "RegistryCountError",
    "RegistryDuplicateError",
    "RegistryExistsError",
    "RegistryIdentifierError",
    "RegistryInvalidRecordError",
    "RegistryListError",
    "RegistryNotFoundError",
    "RegistryReadError",
    "RegistryRecordError",
    "RegistryRemoveError",
    "RegistryReplaceError",
    "RegistryRepositoryConfigurationError",
    "RegistryRepositoryError",
    "RegistryRepositoryOperationError",
    "RegistryStorageError",
    "RegistryUnsupportedOperationError",
]
