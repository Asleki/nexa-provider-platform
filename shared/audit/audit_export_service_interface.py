"""
Nexa Provider Platform
File: shared/audit/audit_export_service_interface.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.7 — Audit Export
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .audit_export_request import AuditExportRequest
from .audit_export_result import AuditExportResult


class AuditExportServiceInterface(ABC):
    """Provider-neutral interface for read-only audit export."""

    @abstractmethod
    def export(self, request: AuditExportRequest) -> AuditExportResult:
        """Transform an approved query result into an export result."""
        raise NotImplementedError


__all__ = ["AuditExportServiceInterface"]
