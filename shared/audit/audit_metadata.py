"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_metadata.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.3.3 — Audit Metadata Aggregate
============================================================

Defines immutable provider-neutral metadata combining actor,
source, runtime and correlation context for an audit record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .audit_actor import AuditActor
from .audit_errors import AuditMetadataError, AuditValidationError
from .audit_source import AuditSource


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
class AuditMetadata:
    """Immutable actor, source, runtime and correlation context."""

    actor: AuditActor
    source: AuditSource
    runtime_id: str
    runtime_mode: str
    correlation_id: str | None = None
    causation_id: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.actor, AuditActor):
            raise AuditMetadataError("actor must be an AuditActor.")

        if not isinstance(self.source, AuditSource):
            raise AuditMetadataError("source must be an AuditSource.")

        object.__setattr__(
            self,
            "runtime_id",
            _normalize_required_text("runtime_id", self.runtime_id),
        )
        object.__setattr__(
            self,
            "runtime_mode",
            _normalize_required_text("runtime_mode", self.runtime_mode),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalize_optional_text(
                "correlation_id",
                self.correlation_id,
            ),
        )
        object.__setattr__(
            self,
            "causation_id",
            _normalize_optional_text("causation_id", self.causation_id),
        )

        if not isinstance(self.attributes, Mapping):
            raise AuditMetadataError("attributes must be a mapping.")

        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(dict(self.attributes)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to a detached plain dictionary."""

        return {
            "actor": self.actor.to_dict(),
            "source": self.source.to_dict(),
            "runtime_id": self.runtime_id,
            "runtime_mode": self.runtime_mode,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "attributes": dict(self.attributes),
        }


__all__ = ["AuditMetadata"]
