"""
Nexa Provider Platform
Registry Repository Ports Public API

Exports only the M008.4 storage-neutral registry repository boundary.
Future identifier, sequence, audit, adapter, factory, and concrete
repository APIs are intentionally not exported here.
"""

from .base_registry_repository import BaseRegistryRepository
from .registry_repository import RegistryRepositoryInterface
from .registry_repository_errors import (
    REGISTRY_REPOSITORY_ERROR_PREFIX,
    RegistryAddError,
    RegistryClearError,
    RegistryCountError,
    RegistryDuplicateError,
    RegistryExistsError,
    RegistryIdentifierError,
    RegistryInvalidRecordError,
    RegistryListError,
    RegistryNotFoundError,
    RegistryReadError,
    RegistryRecordError,
    RegistryRemoveError,
    RegistryReplaceError,
    RegistryRepositoryConfigurationError,
    RegistryRepositoryError,
    RegistryRepositoryOperationError,
    RegistryStorageError,
    RegistryUnsupportedOperationError,
)
from .registry_repository_result import RegistryRepositoryResult
from .registry_repository_types import RegistryRepositoryOperation

__all__ = [
    "REGISTRY_REPOSITORY_ERROR_PREFIX",
    "BaseRegistryRepository",
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
    "RegistryRepositoryInterface",
    "RegistryRepositoryOperation",
    "RegistryRepositoryOperationError",
    "RegistryRepositoryResult",
    "RegistryStorageError",
    "RegistryUnsupportedOperationError",
]
