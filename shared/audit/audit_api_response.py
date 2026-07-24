"""
Nexa Provider Platform
File: shared/audit/audit_api_response.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.8 — Audit API Contracts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .audit_api_operation import AuditApiOperation
from .audit_errors import AuditApiResultError


def _freeze_optional_mapping(
    name: str,
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise AuditApiResultError(f"{name} must be a mapping when provided.")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class AuditApiResponse:
    """Immutable framework-neutral audit API response envelope."""

    request_id: str
    operation: AuditApiOperation
    completed_at: datetime
    success: bool
    data: Mapping[str, Any] | None = None
    error: Mapping[str, Any] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise AuditApiResultError(
                "request_id must be a non-empty string."
            )
        object.__setattr__(self, "request_id", self.request_id.strip())
        try:
            operation = AuditApiOperation.parse(self.operation)
        except Exception as exc:
            raise AuditApiResultError(str(exc)) from exc
        object.__setattr__(self, "operation", operation)

        if not isinstance(self.completed_at, datetime):
            raise AuditApiResultError("completed_at must be a datetime.")
        if self.completed_at.tzinfo is None:
            raise AuditApiResultError(
                "completed_at must be timezone-aware."
            )
        object.__setattr__(
            self, "completed_at", self.completed_at.astimezone(timezone.utc)
        )
        if not isinstance(self.success, bool):
            raise AuditApiResultError("success must be a bool.")

        data = _freeze_optional_mapping("data", self.data)
        error = _freeze_optional_mapping("error", self.error)
        if self.success and error is not None:
            raise AuditApiResultError(
                "successful responses must not contain error."
            )
        if not self.success and data is not None:
            raise AuditApiResultError(
                "failed responses must not contain data."
            )
        if not self.success and error is None:
            raise AuditApiResultError(
                "failed responses must contain error."
            )
        if not isinstance(self.metadata, Mapping):
            raise AuditApiResultError("metadata must be a mapping.")

        object.__setattr__(self, "data", data)
        object.__setattr__(self, "error", error)
        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata))
        )

    @classmethod
    def succeeded(
        cls,
        *,
        request_id: str,
        operation: AuditApiOperation,
        completed_at: datetime,
        data: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditApiResponse":
        return cls(
            request_id=request_id,
            operation=operation,
            completed_at=completed_at,
            success=True,
            data={} if data is None else data,
            metadata={} if metadata is None else metadata,
        )

    @classmethod
    def failed(
        cls,
        *,
        request_id: str,
        operation: AuditApiOperation,
        completed_at: datetime,
        error: Mapping[str, Any],
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditApiResponse":
        return cls(
            request_id=request_id,
            operation=operation,
            completed_at=completed_at,
            success=False,
            error=error,
            metadata={} if metadata is None else metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "completed_at": self.completed_at.isoformat(),
            "success": self.success,
            "data": None if self.data is None else dict(self.data),
            "error": None if self.error is None else dict(self.error),
            "metadata": dict(self.metadata),
        }


__all__ = ["AuditApiResponse"]
