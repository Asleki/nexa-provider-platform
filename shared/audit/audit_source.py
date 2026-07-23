"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_source.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.3.2 — Audit Source Metadata
============================================================

Defines immutable provider-neutral metadata describing where an
audited operation originated and how it can be traced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .audit_errors import AuditMetadataError, AuditValidationError


def _normalize_required_text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise AuditValidationError(f"{name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise AuditValidationError(f"{name} must not be empty.")

    return normalized


def _normalize_optional_text(name: str, value: str | None) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise AuditValidationError(f"{name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise AuditValidationError(
            f"{name} must not be empty when provided."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class AuditSource:
    """Immutable origin and trace metadata for an audited operation."""

    source: str
    source_type: str | None = None
    source_id: str | None = None
    request_id: str | None = None
    device_id: str | None = None
    event_id: str | None = None
    event_type: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source",
            _normalize_required_text("source", self.source),
        )

        for field_name in (
            "source_type",
            "source_id",
            "request_id",
            "device_id",
            "event_id",
            "event_type",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_text(
                    field_name,
                    getattr(self, field_name),
                ),
            )

        if (self.event_id is None) != (self.event_type is None):
            raise AuditValidationError(
                "event_id and event_type must be provided together."
            )

        if not isinstance(self.attributes, Mapping):
            raise AuditMetadataError("attributes must be a mapping.")

        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(dict(self.attributes)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize source metadata to a detached plain dictionary."""

        return {
            "source": self.source,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "request_id": self.request_id,
            "device_id": self.device_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "attributes": dict(self.attributes),
        }


__all__ = ["AuditSource"]
