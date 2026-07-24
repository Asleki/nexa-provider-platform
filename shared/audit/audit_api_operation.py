"""
Nexa Provider Platform
File: shared/audit/audit_api_operation.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.8 — Audit API Contracts
"""
from __future__ import annotations

from enum import Enum

from .audit_errors import AuditApiValidationError


class AuditApiOperation(str, Enum):
    """Stable provider-neutral operation names exposed by the audit API."""

    QUERY = "query"
    VALIDATE_INTEGRITY = "validate_integrity"
    EXPORT = "export"

    @classmethod
    def parse(cls, value: "AuditApiOperation | str") -> "AuditApiOperation":
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise AuditApiValidationError(
                "operation must be an AuditApiOperation or string."
            )
        normalized = value.strip().lower()
        if not normalized:
            raise AuditApiValidationError("operation must not be empty.")
        try:
            return cls(normalized)
        except ValueError as exc:
            raise AuditApiValidationError(
                f"Unsupported audit API operation: {value!r}."
            ) from exc


__all__ = ["AuditApiOperation"]
