"""
Nexa Provider Platform
File: shared/audit/audit_export_request.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.7 — Audit Export
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .audit_errors import AuditExportValidationError
from .audit_query_result import AuditQueryResult


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise AuditExportValidationError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise AuditExportValidationError(f"{name} must not be empty.")
    return normalized


@dataclass(frozen=True, slots=True)
class AuditExportRequest:
    """Immutable request describing one deterministic audit export."""

    export_id: str
    generated_at: datetime
    query_result: AuditQueryResult
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "export_id",
            _required_text("export_id", self.export_id),
        )
        if not isinstance(self.generated_at, datetime):
            raise AuditExportValidationError(
                "generated_at must be a datetime."
            )
        if self.generated_at.tzinfo is None:
            raise AuditExportValidationError(
                "generated_at must be timezone-aware."
            )
        if not isinstance(self.query_result, AuditQueryResult):
            raise AuditExportValidationError(
                "query_result must be an AuditQueryResult."
            )
        if not isinstance(self.metadata, Mapping):
            raise AuditExportValidationError(
                "metadata must be a mapping."
            )
        object.__setattr__(
            self,
            "generated_at",
            self.generated_at.astimezone(timezone.utc),
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


__all__ = ["AuditExportRequest"]
