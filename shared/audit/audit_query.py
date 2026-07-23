"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_query.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.5 — Audit Query Service
============================================================

Defines immutable, provider-neutral criteria for read-only AuditRecord
queries. Supplied criteria are combined using logical AND.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .audit_action import AuditAction
from .audit_errors import AuditQueryValidationError
from .audit_outcome import AuditOutcome


def _optional_text(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise AuditQueryValidationError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise AuditQueryValidationError(
            f"{name} must not be empty when provided."
        )
    return normalized


def _optional_datetime(name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise AuditQueryValidationError(f"{name} must be a datetime.")
    if value.tzinfo is None:
        raise AuditQueryValidationError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class AuditQuery:
    """Validated read-only filters for immutable AuditRecord objects."""

    audit_id: str | None = None
    action: AuditAction | None = None
    outcome: AuditOutcome | None = None
    actor_id: str | None = None
    actor_type: str | None = None
    target_namespace: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    runtime_id: str | None = None
    runtime_mode: str | None = None
    source: str | None = None
    event_id: str | None = None
    event_type: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    request_id: str | None = None
    device_id: str | None = None
    recorded_from: datetime | None = None
    recorded_to: datetime | None = None

    def __post_init__(self) -> None:
        if self.action is not None and not isinstance(self.action, AuditAction):
            raise AuditQueryValidationError(
                "action must be an AuditAction value."
            )
        if self.outcome is not None and not isinstance(
            self.outcome, AuditOutcome
        ):
            raise AuditQueryValidationError(
                "outcome must be an AuditOutcome value."
            )

        text_fields = (
            "audit_id", "actor_id", "actor_type", "target_namespace",
            "target_type", "target_id", "runtime_id", "runtime_mode",
            "source", "event_id", "event_type", "correlation_id",
            "causation_id", "request_id", "device_id",
        )
        for name in text_fields:
            object.__setattr__(
                self, name, _optional_text(name, getattr(self, name))
            )

        object.__setattr__(
            self, "recorded_from",
            _optional_datetime("recorded_from", self.recorded_from),
        )
        object.__setattr__(
            self, "recorded_to",
            _optional_datetime("recorded_to", self.recorded_to),
        )

        if (
            self.recorded_from is not None
            and self.recorded_to is not None
            and self.recorded_from > self.recorded_to
        ):
            raise AuditQueryValidationError(
                "recorded_from must not be later than recorded_to."
            )

    @property
    def is_unfiltered(self) -> bool:
        return all(
            value is None
            for value in (
                self.audit_id, self.action, self.outcome, self.actor_id,
                self.actor_type, self.target_namespace, self.target_type,
                self.target_id, self.runtime_id, self.runtime_mode,
                self.source, self.event_id, self.event_type,
                self.correlation_id, self.causation_id, self.request_id,
                self.device_id, self.recorded_from, self.recorded_to,
            )
        )


__all__ = ["AuditQuery"]
