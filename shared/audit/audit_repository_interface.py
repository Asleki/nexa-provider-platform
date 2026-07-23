"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_repository_interface.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.4 — Audit Repository
============================================================

Defines the storage-independent, append-only AuditRecord repository
contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .audit_record import AuditRecord
from .audit_repository_result import AuditRepositoryResult
from .audit_repository_types import AuditRepositoryType


class AuditRepositoryInterface(ABC):
    """Abstract append-only repository contract for AuditRecord objects."""

    @property
    @abstractmethod
    def repository_name(self) -> str: ...

    @property
    @abstractmethod
    def repository_type(self) -> AuditRepositoryType: ...

    @abstractmethod
    def append(self, record: AuditRecord) -> AuditRepositoryResult: ...

    @abstractmethod
    def get(self, audit_id: str) -> AuditRepositoryResult: ...

    @abstractmethod
    def list_all(self) -> AuditRepositoryResult: ...

    @abstractmethod
    def exists(self, audit_id: str) -> AuditRepositoryResult: ...

    @abstractmethod
    def count(self) -> AuditRepositoryResult: ...


__all__ = ["AuditRepositoryInterface"]
