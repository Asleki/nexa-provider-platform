"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_event_result.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.2.3 — Audit Event Result
============================================================

Defines the standard immutable result returned by audit-event
operations while preserving compatibility with shared EventResult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from shared.events.event_result import EventResult
from shared.events.event_status import EventStatus

from .audit_event_types import AuditEventType


@dataclass(frozen=True, slots=True)
class AuditEventResult:
    """Immutable result for an operation performed on an audit event."""

    audit_id: str
    event_result: EventResult
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.audit_id, str):
            raise TypeError("audit_id must be a string.")

        normalized_audit_id = self.audit_id.strip()
        if not normalized_audit_id:
            raise ValueError("audit_id must not be empty.")

        if not isinstance(self.event_result, EventResult):
            raise TypeError("event_result must be an EventResult.")

        try:
            AuditEventType(self.event_result.event_type)
        except ValueError as exc:
            raise ValueError(
                "event_result.event_type must be a valid AuditEventType value."
            ) from exc

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        object.__setattr__(self, "audit_id", normalized_audit_id)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def success(self) -> bool:
        return self.event_result.success

    @property
    def failed(self) -> bool:
        return self.event_result.failed

    @property
    def event_id(self) -> str:
        return self.event_result.event_id

    @property
    def event_type(self) -> str:
        return self.event_result.event_type

    @property
    def event_status(self) -> EventStatus:
        return self.event_result.event_status

    @property
    def message(self) -> str:
        return self.event_result.message

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "event_result": self.event_result.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def recorded(
        cls,
        *,
        audit_id: str,
        event_id: str,
        message: str = "Audit record event created.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditEventResult":
        return cls(
            audit_id=audit_id,
            event_result=EventResult.created(
                event_id=event_id,
                event_type=AuditEventType.RECORDED.value,
                message=message,
            ),
            metadata=metadata or {},
        )

    @classmethod
    def validated(
        cls,
        *,
        audit_id: str,
        event_id: str,
        message: str = "Audit event validated.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditEventResult":
        return cls(
            audit_id=audit_id,
            event_result=EventResult.validated(
                event_id=event_id,
                event_type=AuditEventType.VALIDATED.value,
                message=message,
            ),
            metadata=metadata or {},
        )

    @classmethod
    def exported(
        cls,
        *,
        audit_id: str,
        event_id: str,
        message: str = "Audit event exported.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditEventResult":
        return cls(
            audit_id=audit_id,
            event_result=EventResult.processed(
                event_id=event_id,
                event_type=AuditEventType.EXPORTED.value,
                message=message,
            ),
            metadata=metadata or {},
        )

    @classmethod
    def archived(
        cls,
        *,
        audit_id: str,
        event_id: str,
        message: str = "Audit event archived.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditEventResult":
        return cls(
            audit_id=audit_id,
            event_result=EventResult.processed(
                event_id=event_id,
                event_type=AuditEventType.ARCHIVED.value,
                message=message,
            ),
            metadata=metadata or {},
        )

    @classmethod
    def purged(
        cls,
        *,
        audit_id: str,
        event_id: str,
        message: str = "Audit event purged.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditEventResult":
        return cls(
            audit_id=audit_id,
            event_result=EventResult.processed(
                event_id=event_id,
                event_type=AuditEventType.PURGED.value,
                message=message,
            ),
            metadata=metadata or {},
        )

    @classmethod
    def failed_result(
        cls,
        *,
        audit_id: str,
        event_id: str,
        event_type: AuditEventType,
        message: str = "Audit event processing failed.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditEventResult":
        if not isinstance(event_type, AuditEventType):
            raise TypeError("event_type must be an AuditEventType value.")

        return cls(
            audit_id=audit_id,
            event_result=EventResult.failed_result(
                event_id=event_id,
                event_type=event_type.value,
                message=message,
            ),
            metadata=metadata or {},
        )

    @classmethod
    def rejected(
        cls,
        *,
        audit_id: str,
        event_id: str,
        event_type: AuditEventType,
        message: str = "Audit event rejected.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "AuditEventResult":
        if not isinstance(event_type, AuditEventType):
            raise TypeError("event_type must be an AuditEventType value.")

        return cls(
            audit_id=audit_id,
            event_result=EventResult.rejected(
                event_id=event_id,
                event_type=event_type.value,
                message=message,
            ),
            metadata=metadata or {},
        )


__all__ = ["AuditEventResult"]
