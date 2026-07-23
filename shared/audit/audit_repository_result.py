"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_repository_result.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.4 — Audit Repository
============================================================

Defines the immutable result returned by successful audit-repository
operations. Failures are represented by audit repository exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .audit_record import AuditRecord
from .audit_repository_types import AuditRepositoryOperation


@dataclass(frozen=True, slots=True)
class AuditRepositoryResult:
    """Standard immutable result for successful repository operations."""

    success: bool
    operation: AuditRepositoryOperation
    repository: str
    audit_id: str | None = None
    record: AuditRecord | None = None
    records: tuple[AuditRecord, ...] = ()
    records_affected: int = 0
    count: int | None = None
    exists: bool | None = None
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")
        if not isinstance(self.operation, AuditRepositoryOperation):
            raise TypeError("operation must be an AuditRepositoryOperation.")
        if not isinstance(self.repository, str):
            raise TypeError("repository must be a string.")
        repository = self.repository.strip()
        if not repository:
            raise ValueError("repository must not be empty.")
        if self.audit_id is not None:
            if not isinstance(self.audit_id, str):
                raise TypeError("audit_id must be a string.")
            audit_id = self.audit_id.strip()
            if not audit_id:
                raise ValueError("audit_id must not be empty when provided.")
        else:
            audit_id = None
        if self.record is not None and not isinstance(self.record, AuditRecord):
            raise TypeError("record must be an AuditRecord.")
        records = tuple(self.records)
        if any(not isinstance(item, AuditRecord) for item in records):
            raise TypeError("records must contain only AuditRecord objects.")
        if isinstance(self.records_affected, bool) or not isinstance(self.records_affected, int):
            raise TypeError("records_affected must be an integer.")
        if self.records_affected < 0:
            raise ValueError("records_affected must not be negative.")
        if self.count is not None:
            if isinstance(self.count, bool) or not isinstance(self.count, int):
                raise TypeError("count must be an integer.")
            if self.count < 0:
                raise ValueError("count must not be negative.")
        if self.exists is not None and not isinstance(self.exists, bool):
            raise TypeError("exists must be a boolean.")
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        if self.record is not None:
            if audit_id is not None and audit_id != self.record.audit_id:
                raise ValueError("audit_id must match record.audit_id.")
            audit_id = self.record.audit_id
        object.__setattr__(self, "repository", repository)
        object.__setattr__(self, "audit_id", audit_id)
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def appended(cls, *, repository: str, record: AuditRecord, metadata: Mapping[str, Any] | None = None) -> "AuditRepositoryResult":
        return cls(True, AuditRepositoryOperation.APPEND, repository, record=record, records_affected=1, message="AuditRecord appended.", metadata=metadata or {})

    @classmethod
    def found(cls, *, repository: str, record: AuditRecord, metadata: Mapping[str, Any] | None = None) -> "AuditRepositoryResult":
        return cls(True, AuditRepositoryOperation.READ, repository, record=record, records_affected=1, message="AuditRecord found.", metadata=metadata or {})

    @classmethod
    def listed(cls, *, repository: str, records: tuple[AuditRecord, ...], metadata: Mapping[str, Any] | None = None) -> "AuditRepositoryResult":
        normalized = tuple(records)
        return cls(True, AuditRepositoryOperation.LIST, repository, records=normalized, records_affected=len(normalized), count=len(normalized), message="AuditRecords listed.", metadata=metadata or {})

    @classmethod
    def existence_checked(cls, *, repository: str, audit_id: str, exists: bool, metadata: Mapping[str, Any] | None = None) -> "AuditRepositoryResult":
        return cls(True, AuditRepositoryOperation.EXISTS, repository, audit_id=audit_id, exists=exists, message="AuditRecord existence checked.", metadata=metadata or {})

    @classmethod
    def counted(cls, *, repository: str, count: int, metadata: Mapping[str, Any] | None = None) -> "AuditRepositoryResult":
        return cls(True, AuditRepositoryOperation.COUNT, repository, records_affected=count, count=count, message="AuditRecords counted.", metadata=metadata or {})


__all__ = ["AuditRepositoryResult"]
