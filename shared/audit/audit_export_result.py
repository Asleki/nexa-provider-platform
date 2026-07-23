"""
Nexa Provider Platform
File: shared/audit/audit_export_result.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.7 — Audit Export
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .audit_errors import AuditExportResultError


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class AuditExportResult:
    """Immutable provider-neutral audit export representation."""

    export_id: str
    generated_at: datetime
    schema_version: int
    records: tuple[Mapping[str, Any], ...] = ()
    query: Mapping[str, Any] = field(default_factory=dict)
    query_metadata: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.export_id, str) or not self.export_id.strip():
            raise AuditExportResultError(
                "export_id must be a non-empty string."
            )
        if not isinstance(self.generated_at, datetime):
            raise AuditExportResultError(
                "generated_at must be a datetime."
            )
        if self.generated_at.tzinfo is None:
            raise AuditExportResultError(
                "generated_at must be timezone-aware."
            )
        if isinstance(self.schema_version, bool) or not isinstance(
            self.schema_version, int
        ):
            raise AuditExportResultError(
                "schema_version must be an integer."
            )
        if self.schema_version < 1:
            raise AuditExportResultError(
                "schema_version must be greater than zero."
            )
        if not isinstance(self.records, tuple):
            raise AuditExportResultError("records must be a tuple.")
        if any(not isinstance(record, Mapping) for record in self.records):
            raise AuditExportResultError(
                "records must contain only mappings."
            )
        for name, value in (
            ("query", self.query),
            ("query_metadata", self.query_metadata),
            ("metadata", self.metadata),
        ):
            if not isinstance(value, Mapping):
                raise AuditExportResultError(f"{name} must be a mapping.")

        object.__setattr__(self, "export_id", self.export_id.strip())
        object.__setattr__(
            self,
            "generated_at",
            self.generated_at.astimezone(timezone.utc),
        )
        object.__setattr__(
            self,
            "records",
            tuple(_freeze_mapping(record) for record in self.records),
        )
        object.__setattr__(self, "query", _freeze_mapping(self.query))
        object.__setattr__(
            self,
            "query_metadata",
            _freeze_mapping(self.query_metadata),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @property
    def count(self) -> int:
        return len(self.records)

    @property
    def empty(self) -> bool:
        return not self.records

    def to_dict(self) -> dict[str, Any]:
        """Return a detached plain representation suitable for adapters."""

        return {
            "export_id": self.export_id,
            "generated_at": self.generated_at.isoformat(),
            "schema_version": self.schema_version,
            "record_count": self.count,
            "query": dict(self.query),
            "query_metadata": dict(self.query_metadata),
            "metadata": dict(self.metadata),
            "records": [dict(record) for record in self.records],
        }


__all__ = ["AuditExportResult"]
