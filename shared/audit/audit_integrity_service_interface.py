"""
Nexa Provider Platform
File: shared/audit/audit_integrity_service_interface.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.6 — Audit Integrity Validation
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .audit_integrity_result import AuditIntegrityResult
from .audit_record import AuditRecord


class AuditIntegrityServiceInterface(ABC):
    """Application-facing, storage-independent integrity contract."""

    @abstractmethod
    def validate_record(self, record: AuditRecord) -> AuditIntegrityResult:
        ...

    @abstractmethod
    def validate_records(
        self,
        records: Sequence[AuditRecord],
    ) -> AuditIntegrityResult:
        ...


__all__ = ["AuditIntegrityServiceInterface"]
