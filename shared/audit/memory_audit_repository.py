"""
============================================================
Nexa Provider Platform
File: shared/audit/memory_audit_repository.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.4 — Audit Repository
============================================================

Provides a thread-safe, deterministic, append-only in-memory
repository for immutable AuditRecord objects.
"""

from __future__ import annotations

from threading import RLock

from .audit_errors import (
    AuditAppendError,
    AuditCountError,
    AuditDuplicateRecordError,
    AuditExistsError,
    AuditListError,
    AuditReadError,
    AuditRecordNotFoundError,
    AuditRepositoryError,
)
from .audit_record import AuditRecord
from .audit_repository_result import AuditRepositoryResult
from .audit_repository_types import AuditRepositoryOperation, AuditRepositoryType
from .base_audit_repository import BaseAuditRepository


class MemoryAuditRepository(BaseAuditRepository):
    """Thread-safe append-only in-memory AuditRecord repository."""

    def __init__(self, repository_name: str = "memory_audit_repository") -> None:
        super().__init__(repository_name=repository_name, repository_type=AuditRepositoryType.MEMORY)
        self._records: dict[str, AuditRecord] = {}
        self._lock = RLock()

    def append(self, record: AuditRecord) -> AuditRepositoryResult:
        operation = AuditRepositoryOperation.APPEND
        try:
            validated = self.validate_record(record, operation=operation)
            with self._lock:
                if validated.audit_id in self._records:
                    raise AuditDuplicateRecordError("AuditRecord with this audit_id already exists.", audit_id=validated.audit_id, action=operation.value, metadata={"repository": self.repository_name})
                self._records[validated.audit_id] = validated
            return AuditRepositoryResult.appended(repository=self.repository_name, record=validated, metadata={"repository_type": self.repository_type.value})
        except AuditRepositoryError:
            raise
        except Exception as exc:
            raise AuditAppendError("AuditRecord could not be appended.", audit_id=record.audit_id if isinstance(record, AuditRecord) else None, action=operation.value, metadata={"repository": self.repository_name, "cause": exc.__class__.__name__}) from exc

    def get(self, audit_id: str) -> AuditRepositoryResult:
        operation = AuditRepositoryOperation.READ
        normalized = self.validate_audit_id(audit_id, operation=operation)
        try:
            with self._lock:
                record = self._records.get(normalized)
            if record is None:
                raise AuditRecordNotFoundError("AuditRecord was not found.", audit_id=normalized, action=operation.value, metadata={"repository": self.repository_name})
            return AuditRepositoryResult.found(repository=self.repository_name, record=record, metadata={"repository_type": self.repository_type.value})
        except AuditRepositoryError:
            raise
        except Exception as exc:
            raise AuditReadError("AuditRecord could not be read.", audit_id=normalized, action=operation.value, metadata={"repository": self.repository_name, "cause": exc.__class__.__name__}) from exc

    def list_all(self) -> AuditRepositoryResult:
        operation = AuditRepositoryOperation.LIST
        try:
            with self._lock:
                records = tuple(self._records.values())
            return AuditRepositoryResult.listed(repository=self.repository_name, records=records, metadata={"repository_type": self.repository_type.value})
        except AuditRepositoryError:
            raise
        except Exception as exc:
            raise AuditListError("AuditRecords could not be listed.", action=operation.value, metadata={"repository": self.repository_name, "cause": exc.__class__.__name__}) from exc

    def exists(self, audit_id: str) -> AuditRepositoryResult:
        operation = AuditRepositoryOperation.EXISTS
        normalized = self.validate_audit_id(audit_id, operation=operation)
        try:
            with self._lock:
                found = normalized in self._records
            return AuditRepositoryResult.existence_checked(repository=self.repository_name, audit_id=normalized, exists=found, metadata={"repository_type": self.repository_type.value})
        except AuditRepositoryError:
            raise
        except Exception as exc:
            raise AuditExistsError("AuditRecord existence could not be checked.", audit_id=normalized, action=operation.value, metadata={"repository": self.repository_name, "cause": exc.__class__.__name__}) from exc

    def count(self) -> AuditRepositoryResult:
        operation = AuditRepositoryOperation.COUNT
        try:
            with self._lock:
                count = len(self._records)
            return AuditRepositoryResult.counted(repository=self.repository_name, count=count, metadata={"repository_type": self.repository_type.value})
        except AuditRepositoryError:
            raise
        except Exception as exc:
            raise AuditCountError("AuditRecords could not be counted.", action=operation.value, metadata={"repository": self.repository_name, "cause": exc.__class__.__name__}) from exc


__all__ = ["MemoryAuditRepository"]
