"""
============================================================
Nexa Provider Platform
File: shared/repositories/local_repository.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Concrete local-file repository implementation.

Each repository collection is stored at:

    storage/local/providers/<repository_name>.json

Higher layers provide only the logical repository name and never
depend on filesystem paths or storage-adapter details.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from shared.storage.storage_manager import StorageManager

from .base_repository import BaseRepository
from .repository_errors import (
    RepositoryConfigurationError,
    RepositoryCountError,
    RepositoryCreateError,
    RepositoryDataCorruptionError,
    RepositoryDeleteError,
    RepositoryDuplicateRecordError,
    RepositoryExistsError,
    RepositoryIdentifierError,
    RepositoryImmutableIdentifierError,
    RepositoryInvalidRecordError,
    RepositoryListError,
    RepositoryReadError,
    RepositoryRecordNotFoundError,
    RepositoryStorageError,
    RepositoryUpdateError,
)
from .repository_result import RepositoryResult
from .repository_types import RepositoryOperation, RepositoryType


DEFAULT_LOCAL_PROVIDER_ROOT = Path("storage/local/providers")


class LocalRepository(BaseRepository):
    """
    JSON collection repository backed by ``StorageManager``.
    """

    def __init__(
        self,
        storage_manager: StorageManager,
        repository_name: str,
        id_field: str,
        *,
        storage_root: str | Path = DEFAULT_LOCAL_PROVIDER_ROOT,
        backend: str | None = None,
    ) -> None:
        if not isinstance(storage_manager, StorageManager):
            raise RepositoryConfigurationError(
                "storage_manager must be a StorageManager instance.",
                repository=repository_name,
                repository_type=RepositoryType.LOCAL.value,
            )

        normalized_name = str(repository_name).strip()

        if (
            not normalized_name
            or normalized_name in {".", ".."}
            or "/" in normalized_name
            or "\\" in normalized_name
            or Path(normalized_name).name != normalized_name
        ):
            raise RepositoryConfigurationError(
                "repository_name must be a safe collection name.",
                repository=normalized_name or None,
                repository_type=RepositoryType.LOCAL.value,
            )

        root = Path(storage_root)

        super().__init__(
            repository_name=normalized_name,
            id_field=id_field,
            repository_type=RepositoryType.LOCAL,
        )

        self._storage_manager = storage_manager
        self._storage_root = root
        self._backend = backend
        self._collection_path = root / f"{normalized_name}.json"

    @property
    def collection_path(self) -> Path:
        return self._collection_path

    @property
    def backend(self) -> str | None:
        return self._backend

    def create(self, record: Mapping[str, Any]) -> RepositoryResult:
        operation = RepositoryOperation.CREATE

        try:
            normalized_record = self._normalize_record(record)
            record_id = self._record_identifier(normalized_record)
            records = self._load_records(operation)

            if self._find_index(records, record_id) is not None:
                raise RepositoryDuplicateRecordError(
                    f"Record already exists: {record_id}",
                    operation=operation,
                    repository=self.repository_name,
                    record_id=record_id,
                    repository_type=self.repository_type,
                )

            records.append(normalized_record)
            self._persist_records(records, operation, record_id=record_id)

            return RepositoryResult.created(
                repository=self.repository_name,
                record_id=record_id,
                record=normalized_record,
                metadata=self._result_metadata(),
            )
        except (
            RepositoryDuplicateRecordError,
            RepositoryIdentifierError,
            RepositoryInvalidRecordError,
            RepositoryDataCorruptionError,
        ):
            raise
        except Exception as exc:
            raise RepositoryCreateError(
                "Unable to create repository record.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

    def get(self, record_id: Any) -> RepositoryResult:
        operation = RepositoryOperation.READ
        normalized_id = self._normalize_identifier(record_id, operation)

        try:
            records = self._load_records(operation)
            index = self._find_index(records, normalized_id)

            if index is None:
                raise RepositoryRecordNotFoundError(
                    f"Record not found: {normalized_id}",
                    operation=operation,
                    repository=self.repository_name,
                    record_id=normalized_id,
                    repository_type=self.repository_type,
                )

            return RepositoryResult.found(
                repository=self.repository_name,
                record_id=normalized_id,
                record=records[index],
                metadata=self._result_metadata(),
            )
        except (
            RepositoryRecordNotFoundError,
            RepositoryDataCorruptionError,
        ):
            raise
        except Exception as exc:
            raise RepositoryReadError(
                "Unable to read repository record.",
                operation=operation,
                repository=self.repository_name,
                record_id=normalized_id,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

    def update(
        self,
        record_id: Any,
        record: Mapping[str, Any],
    ) -> RepositoryResult:
        operation = RepositoryOperation.UPDATE
        normalized_id = self._normalize_identifier(record_id, operation)

        try:
            changes = self._normalize_record(record, require_identifier=False)

            if not changes:
                raise RepositoryInvalidRecordError(
                    "Repository update must contain at least one field.",
                    operation=operation,
                    repository=self.repository_name,
                    record_id=normalized_id,
                    repository_type=self.repository_type,
                )

            if self.id_field in changes:
                supplied_id = self._normalize_identifier(
                    changes[self.id_field],
                    operation,
                )
                if supplied_id != normalized_id:
                    raise RepositoryImmutableIdentifierError(
                        f"Immutable identifier '{self.id_field}' cannot be changed.",
                        operation=operation,
                        repository=self.repository_name,
                        record_id=normalized_id,
                        repository_type=self.repository_type,
                    )

            records = self._load_records(operation)
            index = self._find_index(records, normalized_id)

            if index is None:
                raise RepositoryRecordNotFoundError(
                    f"Record not found: {normalized_id}",
                    operation=operation,
                    repository=self.repository_name,
                    record_id=normalized_id,
                    repository_type=self.repository_type,
                )

            updated_record = dict(records[index])
            updated_record.update(changes)
            updated_record[self.id_field] = normalized_id
            records[index] = updated_record

            self._persist_records(
                records,
                operation,
                record_id=normalized_id,
            )

            return RepositoryResult.updated(
                repository=self.repository_name,
                record_id=normalized_id,
                record=updated_record,
                metadata=self._result_metadata(),
            )
        except (
            RepositoryRecordNotFoundError,
            RepositoryIdentifierError,
            RepositoryImmutableIdentifierError,
            RepositoryInvalidRecordError,
            RepositoryDataCorruptionError,
        ):
            raise
        except Exception as exc:
            raise RepositoryUpdateError(
                "Unable to update repository record.",
                operation=operation,
                repository=self.repository_name,
                record_id=normalized_id,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

    def delete(self, record_id: Any) -> RepositoryResult:
        operation = RepositoryOperation.DELETE
        normalized_id = self._normalize_identifier(record_id, operation)

        try:
            records = self._load_records(operation)
            index = self._find_index(records, normalized_id)

            if index is None:
                raise RepositoryRecordNotFoundError(
                    f"Record not found: {normalized_id}",
                    operation=operation,
                    repository=self.repository_name,
                    record_id=normalized_id,
                    repository_type=self.repository_type,
                )

            records.pop(index)
            self._persist_records(
                records,
                operation,
                record_id=normalized_id,
            )

            return RepositoryResult.deleted(
                repository=self.repository_name,
                record_id=normalized_id,
                metadata=self._result_metadata(),
            )
        except (
            RepositoryRecordNotFoundError,
            RepositoryDataCorruptionError,
        ):
            raise
        except Exception as exc:
            raise RepositoryDeleteError(
                "Unable to delete repository record.",
                operation=operation,
                repository=self.repository_name,
                record_id=normalized_id,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

    def list_all(self) -> RepositoryResult:
        operation = RepositoryOperation.LIST

        try:
            records = self._load_records(operation)

            return RepositoryResult.listed(
                repository=self.repository_name,
                records=tuple(records),
                metadata=self._result_metadata(),
            )
        except RepositoryDataCorruptionError:
            raise
        except Exception as exc:
            raise RepositoryListError(
                "Unable to list repository records.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

    def exists(self, record_id: Any) -> RepositoryResult:
        operation = RepositoryOperation.EXISTS
        normalized_id = self._normalize_identifier(record_id, operation)

        try:
            records = self._load_records(operation)
            exists = self._find_index(records, normalized_id) is not None

            return RepositoryResult.existence_checked(
                repository=self.repository_name,
                record_id=normalized_id,
                exists=exists,
                metadata=self._result_metadata(),
            )
        except RepositoryDataCorruptionError:
            raise
        except Exception as exc:
            raise RepositoryExistsError(
                "Unable to check repository record existence.",
                operation=operation,
                repository=self.repository_name,
                record_id=normalized_id,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

    def count(self) -> RepositoryResult:
        operation = RepositoryOperation.COUNT

        try:
            records = self._load_records(operation)

            return RepositoryResult.counted(
                repository=self.repository_name,
                count=len(records),
                metadata=self._result_metadata(),
            )
        except RepositoryDataCorruptionError:
            raise
        except Exception as exc:
            raise RepositoryCountError(
                "Unable to count repository records.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

    def _load_records(
        self,
        operation: RepositoryOperation,
    ) -> list[dict[str, Any]]:
        try:
            if not self._storage_manager.exists(
                self.collection_path,
                backend=self.backend,
            ):
                return []

            data = self._storage_manager.read(
                self.collection_path,
                backend=self.backend,
            )
        except Exception as exc:
            raise RepositoryStorageError(
                "Unable to access persisted repository data.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
                metadata=self._result_metadata(),
            ) from exc

        if data is None:
            return []

        if not isinstance(data, list):
            raise RepositoryDataCorruptionError(
                "Repository collection must contain a JSON array.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                metadata={
                    **self._result_metadata(),
                    "actual_type": type(data).__name__,
                },
            )

        records: list[dict[str, Any]] = []
        seen_identifiers: set[str] = set()

        for position, item in enumerate(data):
            if not isinstance(item, Mapping):
                raise RepositoryDataCorruptionError(
                    "Repository collection contains a non-object record.",
                    operation=operation,
                    repository=self.repository_name,
                    repository_type=self.repository_type,
                    metadata={
                        **self._result_metadata(),
                        "record_position": position,
                        "actual_type": type(item).__name__,
                    },
                )

            normalized_record = dict(item)

            try:
                record_id = self._record_identifier(normalized_record)
            except (
                RepositoryIdentifierError,
                RepositoryInvalidRecordError,
            ) as exc:
                raise RepositoryDataCorruptionError(
                    "Persisted repository record has an invalid identifier.",
                    operation=operation,
                    repository=self.repository_name,
                    repository_type=self.repository_type,
                    cause=exc,
                    metadata={
                        **self._result_metadata(),
                        "record_position": position,
                    },
                ) from exc

            if record_id in seen_identifiers:
                raise RepositoryDataCorruptionError(
                    f"Duplicate persisted identifier: {record_id}",
                    operation=operation,
                    repository=self.repository_name,
                    record_id=record_id,
                    repository_type=self.repository_type,
                    metadata={
                        **self._result_metadata(),
                        "record_position": position,
                    },
                )

            normalized_record[self.id_field] = record_id
            seen_identifiers.add(record_id)
            records.append(normalized_record)

        return records

    def _persist_records(
        self,
        records: list[dict[str, Any]],
        operation: RepositoryOperation,
        *,
        record_id: str | None = None,
    ) -> None:
        try:
            result = self._storage_manager.write(
                self.collection_path,
                records,
                overwrite=True,
                backend=self.backend,
            )
        except Exception as exc:
            raise self._operation_error(
                operation,
                "Storage write failed.",
                record_id=record_id,
                cause=exc,
            ) from exc

        if result.failed:
            raise self._operation_error(
                operation,
                result.message or "Storage write returned a failed result.",
                record_id=record_id,
                metadata={
                    **self._result_metadata(),
                    "storage_operation": result.operation,
                    "storage_result": result.to_dict(),
                },
            )

    def _normalize_record(
        self,
        record: Mapping[str, Any],
        *,
        require_identifier: bool = True,
    ) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise RepositoryInvalidRecordError(
                "Repository record must be a mapping.",
                repository=self.repository_name,
                repository_type=self.repository_type,
                metadata={"actual_type": type(record).__name__},
            )

        normalized = dict(record)

        if require_identifier:
            record_id = self._record_identifier(normalized)
            normalized[self.id_field] = record_id

        return normalized

    def _record_identifier(self, record: Mapping[str, Any]) -> str:
        if self.id_field not in record:
            raise RepositoryInvalidRecordError(
                f"Record is missing identifier field: {self.id_field}",
                repository=self.repository_name,
                repository_type=self.repository_type,
            )

        return self._normalize_identifier(record[self.id_field], None)

    def _normalize_identifier(
        self,
        record_id: Any,
        operation: RepositoryOperation | None,
    ) -> str:
        try:
            return self.validate_identifier(record_id)
        except (TypeError, ValueError) as exc:
            raise RepositoryIdentifierError(
                "Repository identifier must not be empty.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def _find_index(
        self,
        records: list[dict[str, Any]],
        record_id: str,
    ) -> int | None:
        for index, record in enumerate(records):
            if record[self.id_field] == record_id:
                return index

        return None

    def _result_metadata(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "repository_type": self.repository_type,
            "collection_path": str(self.collection_path),
        }

        if self.backend is not None:
            metadata["backend"] = self.backend

        return metadata

    def _operation_error(
        self,
        operation: RepositoryOperation,
        message: str,
        *,
        record_id: str | None = None,
        cause: BaseException | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Exception:
        error_types = {
            RepositoryOperation.CREATE: RepositoryCreateError,
            RepositoryOperation.READ: RepositoryReadError,
            RepositoryOperation.UPDATE: RepositoryUpdateError,
            RepositoryOperation.DELETE: RepositoryDeleteError,
            RepositoryOperation.LIST: RepositoryListError,
            RepositoryOperation.EXISTS: RepositoryExistsError,
            RepositoryOperation.COUNT: RepositoryCountError,
        }
        error_type = error_types[operation]

        return error_type(
            message,
            operation=operation,
            repository=self.repository_name,
            record_id=record_id,
            repository_type=self.repository_type,
            cause=cause,
            metadata=metadata or self._result_metadata(),
        )


__all__ = [
    "DEFAULT_LOCAL_PROVIDER_ROOT",
    "LocalRepository",
]
