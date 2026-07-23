"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_record.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.1.4 — Audit Record Contract
============================================================

Defines the immutable canonical record produced by the Shared
Audit Infrastructure.

An AuditRecord captures who performed an action, what resource
was affected, the final outcome, the runtime and source context,
and optional event-trace identifiers. It is provider-neutral and
contains no repository, storage, or backend-specific behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .audit_action import AuditAction
from .audit_errors import (
    AuditIdentifierError,
    AuditMetadataError,
    AuditTimestampError,
    AuditValidationError,
)
from .audit_outcome import AuditOutcome


def _normalize_required_text(name: str, value: str) -> str:
    """Validate and normalize a required string field."""

    if not isinstance(value, str):
        raise AuditValidationError(f"{name} must be a string.")

    normalized = value.strip()

    if not normalized:
        raise AuditValidationError(f"{name} must not be empty.")

    return normalized


def _normalize_optional_text(
    name: str,
    value: str | None,
) -> str | None:
    """Validate and normalize an optional string field."""

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
class AuditRecord:
    """
    Immutable provider-neutral audit record.

    Required fields establish the audit identity, action, outcome,
    actor, target, runtime and source. Optional traceability fields
    connect the record to events, requests and devices when those
    identifiers are available.
    """

    audit_id: str
    version: int
    recorded_at: datetime

    action: AuditAction
    outcome: AuditOutcome

    actor_id: str
    actor_type: str

    target_namespace: str
    target_type: str
    target_id: str

    runtime_id: str
    runtime_mode: str

    source: str

    event_id: str | None = None
    event_type: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    request_id: str | None = None
    device_id: str | None = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            normalized_audit_id = _normalize_required_text(
                "audit_id",
                self.audit_id,
            )
        except AuditValidationError as exc:
            raise AuditIdentifierError(
                exc.message,
                audit_id=(
                    self.audit_id.strip()
                    if isinstance(self.audit_id, str)
                    and self.audit_id.strip()
                    else None
                ),
            ) from exc

        if isinstance(self.version, bool) or not isinstance(
            self.version,
            int,
        ):
            raise AuditValidationError(
                "version must be an integer.",
                audit_id=normalized_audit_id,
            )

        if self.version < 1:
            raise AuditValidationError(
                "version must be greater than zero.",
                audit_id=normalized_audit_id,
            )

        if not isinstance(self.recorded_at, datetime):
            raise AuditTimestampError(
                "recorded_at must be a datetime.",
                audit_id=normalized_audit_id,
            )

        if self.recorded_at.tzinfo is None:
            raise AuditTimestampError(
                "recorded_at must be timezone-aware.",
                audit_id=normalized_audit_id,
            )

        if not isinstance(self.action, AuditAction):
            raise AuditValidationError(
                "action must be an AuditAction value.",
                audit_id=normalized_audit_id,
            )

        if not isinstance(self.outcome, AuditOutcome):
            raise AuditValidationError(
                "outcome must be an AuditOutcome value.",
                audit_id=normalized_audit_id,
                action=self.action.value,
            )

        normalized_required = {
            "actor_id": _normalize_required_text(
                "actor_id",
                self.actor_id,
            ),
            "actor_type": _normalize_required_text(
                "actor_type",
                self.actor_type,
            ),
            "target_namespace": _normalize_required_text(
                "target_namespace",
                self.target_namespace,
            ),
            "target_type": _normalize_required_text(
                "target_type",
                self.target_type,
            ),
            "target_id": _normalize_required_text(
                "target_id",
                self.target_id,
            ),
            "runtime_id": _normalize_required_text(
                "runtime_id",
                self.runtime_id,
            ),
            "runtime_mode": _normalize_required_text(
                "runtime_mode",
                self.runtime_mode,
            ),
            "source": _normalize_required_text(
                "source",
                self.source,
            ),
        }

        normalized_optional = {
            "event_id": _normalize_optional_text(
                "event_id",
                self.event_id,
            ),
            "event_type": _normalize_optional_text(
                "event_type",
                self.event_type,
            ),
            "correlation_id": _normalize_optional_text(
                "correlation_id",
                self.correlation_id,
            ),
            "causation_id": _normalize_optional_text(
                "causation_id",
                self.causation_id,
            ),
            "request_id": _normalize_optional_text(
                "request_id",
                self.request_id,
            ),
            "device_id": _normalize_optional_text(
                "device_id",
                self.device_id,
            ),
        }

        if (normalized_optional["event_id"] is None) != (
            normalized_optional["event_type"] is None
        ):
            raise AuditValidationError(
                "event_id and event_type must be provided together.",
                audit_id=normalized_audit_id,
                action=self.action.value,
            )

        if not isinstance(self.metadata, Mapping):
            raise AuditMetadataError(
                "metadata must be a mapping.",
                audit_id=normalized_audit_id,
                action=self.action.value,
            )

        object.__setattr__(self, "audit_id", normalized_audit_id)
        object.__setattr__(
            self,
            "recorded_at",
            self.recorded_at.astimezone(timezone.utc),
        )

        for field_name, value in normalized_required.items():
            object.__setattr__(self, field_name, value)

        for field_name, value in normalized_optional.items():
            object.__setattr__(self, field_name, value)

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record into a detached plain dictionary."""

        return {
            "audit_id": self.audit_id,
            "version": self.version,
            "recorded_at": self.recorded_at.isoformat(),
            "action": self.action.value,
            "outcome": self.outcome.value,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "target_namespace": self.target_namespace,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "runtime_id": self.runtime_id,
            "runtime_mode": self.runtime_mode,
            "source": self.source,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "request_id": self.request_id,
            "device_id": self.device_id,
            "metadata": dict(self.metadata),
        }


__all__ = ["AuditRecord"]
