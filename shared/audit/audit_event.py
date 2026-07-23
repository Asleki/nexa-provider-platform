"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_event.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.2.2 — Audit Event
============================================================

Defines the immutable event representation used to carry a
canonical AuditRecord through the platform event infrastructure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from shared.events.base_event import BaseEvent

from .audit_errors import AuditValidationError
from .audit_event_types import AuditEventType
from .audit_record import AuditRecord


class AuditEvent(BaseEvent):
    """Immutable event carrying one canonical audit record."""

    def __init__(
        self,
        *,
        event_id: str,
        event_type: AuditEventType,
        occurred_at: datetime,
        record: AuditRecord,
        event_version: int = 1,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if not isinstance(event_type, AuditEventType):
            raise TypeError("event_type must be an AuditEventType value.")

        if not isinstance(record, AuditRecord):
            raise TypeError("record must be an AuditRecord.")

        self._audit_event_type = event_type
        self._record = record

        super().__init__(
            event_id=event_id,
            event_type=event_type.value,
            event_version=event_version,
            occurred_at=occurred_at,
            metadata=metadata,
            payload={"record": record.to_dict()},
        )

    @property
    def audit_event_type(self) -> AuditEventType:
        """Return the typed audit-domain event name."""

        return self._audit_event_type

    @property
    def record(self) -> AuditRecord:
        """Return the immutable canonical audit record."""

        return self._record

    def validate(self) -> None:
        """Validate the shared event contract and audit linkage."""

        super().validate()

        if self.event_type != self.audit_event_type.value:
            raise AuditValidationError(
                "event_type must match audit_event_type.",
                audit_id=self.record.audit_id,
                action=self.record.action.value,
            )


    def to_dict(self) -> dict[str, Any]:
        """Serialize the event into a detached plain dictionary."""

        data = super().to_dict()
        data["payload"] = {"record": self.record.to_dict()}
        return data


__all__ = ["AuditEvent"]
