"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_query_service_interface.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.5 — Audit Query Service
============================================================
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .audit_query import AuditQuery
from .audit_query_result import AuditQueryResult


class AuditQueryServiceInterface(ABC):
    """Storage-independent read-only AuditRecord query contract."""

    @abstractmethod
    def query(self, query: AuditQuery) -> AuditQueryResult: ...


__all__ = ["AuditQueryServiceInterface"]
