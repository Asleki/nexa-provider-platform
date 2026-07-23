"""
============================================================
Nexa Provider Platform
File: shared/audit/base_audit_repository.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.4 — Audit Repository
============================================================

Provides shared identity and input validation for concrete audit
repositories without implementing storage.
"""

from __future__ import annotations

from .audit_errors import AuditInvalidRecordError, AuditRepositoryConfigurationError
from .audit_record import AuditRecord
from .audit_repository_interface import AuditRepositoryInterface
from .audit_repository_types import AuditRepositoryOperation, AuditRepositoryType


class BaseAuditRepository(AuditRepositoryInterface):
    """Base implementation for audit repository identity and validation."""

    def __init__(self, *, repository_name: str, repository_type: AuditRepositoryType) -> None:
        if not isinstance(repository_name, str):
            raise AuditRepositoryConfigurationError("repository_name must be a string.")
        normalized_name = repository_name.strip()
        if not normalized_name:
            raise AuditRepositoryConfigurationError("repository_name must not be empty.")
        if not isinstance(repository_type, AuditRepositoryType):
            raise AuditRepositoryConfigurationError("repository_type must be an AuditRepositoryType.")
        self._repository_name = normalized_name
        self._repository_type = repository_type

    @property
    def repository_name(self) -> str:
        return self._repository_name

    @property
    def repository_type(self) -> AuditRepositoryType:
        return self._repository_type

    def validate_audit_id(self, audit_id: str, *, operation: AuditRepositoryOperation) -> str:
        if not isinstance(operation, AuditRepositoryOperation):
            raise TypeError("operation must be an AuditRepositoryOperation.")
        if not isinstance(audit_id, str):
            raise AuditInvalidRecordError("audit_id must be a string.", action=operation.value, metadata={"repository": self.repository_name})
        normalized = audit_id.strip()
        if not normalized:
            raise AuditInvalidRecordError("audit_id must not be empty.", action=operation.value, metadata={"repository": self.repository_name})
        return normalized

    def validate_record(self, record: AuditRecord, *, operation: AuditRepositoryOperation) -> AuditRecord:
        if not isinstance(operation, AuditRepositoryOperation):
            raise TypeError("operation must be an AuditRepositoryOperation.")
        if not isinstance(record, AuditRecord):
            raise AuditInvalidRecordError("record must be an AuditRecord.", action=operation.value, metadata={"repository": self.repository_name})
        normalized_id = self.validate_audit_id(record.audit_id, operation=operation)
        if normalized_id != record.audit_id:
            raise AuditInvalidRecordError("AuditRecord audit_id must already be normalized.", audit_id=normalized_id, action=operation.value, metadata={"repository": self.repository_name})
        return record


__all__ = ["BaseAuditRepository"]
