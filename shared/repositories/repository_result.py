"""
============================================================
Nexa Provider Platform
File: shared/repositories/repository_result.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Defines the standardized result returned by successful
repository operations.

Repository results provide a predictable contract to higher
layers while repository exceptions represent failed
operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .repository_types import RepositoryOperation


def _freeze_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """
    Return an immutable shallow copy of a mapping.

    A shallow immutable copy prevents callers from modifying
    the result mapping directly after construction.
    """

    if value is None:
        return None

    return MappingProxyType(dict(value))


def _freeze_records(
    records: tuple[Mapping[str, Any], ...],
) -> tuple[Mapping[str, Any], ...]:
    """
    Return an immutable tuple containing immutable mappings.
    """

    return tuple(MappingProxyType(dict(record)) for record in records)


@dataclass(frozen=True, slots=True)
class RepositoryResult:
    """
    Standard result returned by successful repository operations.

    Attributes
    ----------
    success:
        Indicates whether the operation succeeded.

    operation:
        Repository operation that produced this result.

    repository:
        Logical repository name, such as ``citizens``.

    record_id:
        Identifier of the affected or retrieved record.

    record:
        Single record returned by create, read or update.

    records:
        Collection returned by list operations.

    records_affected:
        Number of records affected by the operation.

    message:
        Human-readable result description.

    metadata:
        Additional implementation-neutral context.
    """

    success: bool
    operation: RepositoryOperation
    repository: str
    record_id: str | None = None
    record: Mapping[str, Any] | None = None
    records: tuple[Mapping[str, Any], ...] = ()
    records_affected: int = 0
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize result state."""

        repository = self.repository.strip()

        if not repository:
            raise ValueError("Repository name must not be empty.")

        if self.records_affected < 0:
            raise ValueError(
                "records_affected must not be negative."
            )

        if self.record_id is not None:
            normalized_record_id = self.record_id.strip()

            if not normalized_record_id:
                raise ValueError(
                    "record_id must not be empty when provided."
                )

            object.__setattr__(
                self,
                "record_id",
                normalized_record_id,
            )

        object.__setattr__(self, "repository", repository)
        object.__setattr__(
            self,
            "record",
            _freeze_mapping(self.record),
        )
        object.__setattr__(
            self,
            "records",
            _freeze_records(tuple(self.records)),
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def failed(self) -> bool:
        """Return True when the operation failed."""

        return not self.success

    @property
    def count(self) -> int:
        """
        Return the number of records represented by the result.

        For list operations this is the number of returned records.
        For other operations this is records_affected.
        """

        if self.operation is RepositoryOperation.LIST:
            return len(self.records)

        return self.records_affected

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result into a plain dictionary."""

        return {
            "success": self.success,
            "operation": self.operation.value,
            "repository": self.repository,
            "record_id": self.record_id,
            "record": (
                dict(self.record)
                if self.record is not None
                else None
            ),
            "records": [
                dict(record)
                for record in self.records
            ],
            "records_affected": self.records_affected,
            "message": self.message,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def created(
        cls,
        *,
        repository: str,
        record_id: str,
        record: Mapping[str, Any],
        message: str = "Repository record created.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        """Create a successful create-operation result."""

        return cls(
            success=True,
            operation=RepositoryOperation.CREATE,
            repository=repository,
            record_id=record_id,
            record=record,
            records_affected=1,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def found(
        cls,
        *,
        repository: str,
        record_id: str,
        record: Mapping[str, Any],
        message: str = "Repository record found.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        """Create a successful read-operation result."""

        return cls(
            success=True,
            operation=RepositoryOperation.READ,
            repository=repository,
            record_id=record_id,
            record=record,
            records_affected=1,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def updated(
        cls,
        *,
        repository: str,
        record_id: str,
        record: Mapping[str, Any],
        message: str = "Repository record updated.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        """Create a successful update-operation result."""

        return cls(
            success=True,
            operation=RepositoryOperation.UPDATE,
            repository=repository,
            record_id=record_id,
            record=record,
            records_affected=1,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def deleted(
        cls,
        *,
        repository: str,
        record_id: str,
        message: str = "Repository record deleted.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        """Create a successful delete-operation result."""

        return cls(
            success=True,
            operation=RepositoryOperation.DELETE,
            repository=repository,
            record_id=record_id,
            records_affected=1,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def listed(
        cls,
        *,
        repository: str,
        records: tuple[Mapping[str, Any], ...],
        message: str = "Repository records listed.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        """Create a successful list-operation result."""

        normalized_records = tuple(records)

        return cls(
            success=True,
            operation=RepositoryOperation.LIST,
            repository=repository,
            records=normalized_records,
            records_affected=len(normalized_records),
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def existence_checked(
        cls,
        *,
        repository: str,
        record_id: str,
        exists: bool,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        """Create a successful exists-operation result."""

        combined_metadata = dict(metadata or {})
        combined_metadata["exists"] = exists

        return cls(
            success=True,
            operation=RepositoryOperation.EXISTS,
            repository=repository,
            record_id=record_id,
            records_affected=1 if exists else 0,
            message=(
                "Repository record exists."
                if exists
                else "Repository record does not exist."
            ),
            metadata=combined_metadata,
        )

    @classmethod
    def counted(
        cls,
        *,
        repository: str,
        count: int,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        """Create a successful count-operation result."""

        if count < 0:
            raise ValueError("count must not be negative.")

        combined_metadata = dict(metadata or {})
        combined_metadata["count"] = count

        return cls(
            success=True,
            operation=RepositoryOperation.COUNT,
            repository=repository,
            records_affected=count,
            message="Repository records counted.",
            metadata=combined_metadata,
        )


__all__ = [
    "RepositoryResult",
]

