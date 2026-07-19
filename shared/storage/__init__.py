"""
============================================================
Nexa Provider Platform
Package: shared.storage
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

Public package exports for the Storage Foundation.

This package provides:

- StorageAdapter
- StorageManager
- StoragePaths
- StorageResult
- JsonStorage
- JsonlStorage
- CsvStorage
- Storage exception hierarchy
"""

from .csv_storage import CsvStorage
from .json_storage import JsonStorage
from .jsonl_storage import JsonlStorage
from .storage_adapter import StorageAdapter
from .storage_errors import (
    STORAGE_ERROR_PREFIX,
    StorageAppendError,
    StorageAtomicWriteError,
    StorageBackendError,
    StorageBackendUnavailableError,
    StorageConcurrencyError,
    StorageConfigurationError,
    StorageConflictError,
    StorageCorruptionError,
    StorageDeleteError,
    StorageDeserializationError,
    StorageDirectoryError,
    StorageDuplicateRecordError,
    StorageEncodingError,
    StorageError,
    StorageInitializationError,
    StorageIntegrityError,
    StorageListError,
    StorageOperationNotSupportedError,
    StoragePathError,
    StoragePathExistsError,
    StoragePathNotFoundError,
    StoragePathPermissionError,
    StoragePathTraversalError,
    StorageReadError,
    StorageRecordError,
    StorageRecordNotFoundError,
    StorageSerializationError,
    StorageValidationError,
    StorageWriteError,
    UnsupportedStorageBackendError,
)
from .storage_manager import StorageManager
from .storage_paths import StoragePaths
from .storage_result import StorageResult

__all__ = [
    "CsvStorage",
    "JsonStorage",
    "JsonlStorage",
    "STORAGE_ERROR_PREFIX",
    "StorageAdapter",
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
    "StorageManager",
    "StorageOperationNotSupportedError",
    "StoragePathError",
    "StoragePathExistsError",
    "StoragePathNotFoundError",
    "StoragePathPermissionError",
    "StoragePathTraversalError",
    "StoragePaths",
    "StorageReadError",
    "StorageRecordError",
    "StorageRecordNotFoundError",
    "StorageResult",
    "StorageSerializationError",
    "StorageValidationError",
    "StorageWriteError",
    "UnsupportedStorageBackendError",
]
