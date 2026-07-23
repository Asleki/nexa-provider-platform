"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_query_result.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.5 — Audit Query Service
============================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .audit_errors import AuditQueryResultError
from .audit_query import AuditQuery
from .audit_record import AuditRecord


@dataclass(frozen=True, slots=True)
class AuditQueryResult:
    """Immutable result returned by an Audit Query Service."""

    query: AuditQuery
    records: tuple[AuditRecord, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.query, AuditQuery):
            raise AuditQueryResultError("query must be an AuditQuery.")
        if not isinstance(self.records, tuple):
            raise AuditQueryResultError("records must be a tuple.")
        if any(not isinstance(record, AuditRecord) for record in self.records):
            raise AuditQueryResultError(
                "records must contain only AuditRecord values."
            )
        if not isinstance(self.metadata, Mapping):
            raise AuditQueryResultError("metadata must be a mapping.")
        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata))
        )

    @property
    def count(self) -> int:
        return len(self.records)

    @property
    def found(self) -> bool:
        return bool(self.records)


__all__ = ["AuditQueryResult"]
