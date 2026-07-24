"""
Nexa Provider Platform
File: shared/audit/audit_api_request.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.8 — Audit API Contracts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .audit_api_operation import AuditApiOperation
from .audit_errors import AuditApiValidationError


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise AuditApiValidationError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise AuditApiValidationError(f"{name} must not be empty.")
    return normalized


def _freeze_mapping(name: str, value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuditApiValidationError(f"{name} must be a mapping.")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class AuditApiRequest:
    """Immutable framework-neutral audit API request envelope."""

    request_id: str
    operation: AuditApiOperation
    requested_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "request_id", _required_text("request_id", self.request_id)
        )
        object.__setattr__(
            self, "operation", AuditApiOperation.parse(self.operation)
        )
        if not isinstance(self.requested_at, datetime):
            raise AuditApiValidationError("requested_at must be a datetime.")
        if self.requested_at.tzinfo is None:
            raise AuditApiValidationError(
                "requested_at must be timezone-aware."
            )
        object.__setattr__(
            self, "requested_at", self.requested_at.astimezone(timezone.utc)
        )
        object.__setattr__(
            self, "payload", _freeze_mapping("payload", self.payload)
        )
        object.__setattr__(
            self, "metadata", _freeze_mapping("metadata", self.metadata)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "requested_at": self.requested_at.isoformat(),
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }


__all__ = ["AuditApiRequest"]
