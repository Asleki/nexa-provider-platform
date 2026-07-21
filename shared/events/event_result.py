"""
============================================================
Nexa Provider Platform
File: shared/events/event_result.py
Layer: Shared Event Infrastructure
Milestone: NPP-M006.1.3 — Event Result
Revision: v2
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .event_status import EventStatus


@dataclass(frozen=True, slots=True)
class EventResult:
    """Standard result returned by event-processing operations."""

    success: bool
    event_id: str
    event_type: str
    event_status: EventStatus
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.event_id, str):
            raise TypeError("event_id must be a string.")

        normalized_event_id = self.event_id.strip()
        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        if not isinstance(self.event_type, str):
            raise TypeError("event_type must be a string.")

        normalized_event_type = self.event_type.strip()
        if not normalized_event_type:
            raise ValueError("event_type must not be empty.")

        if not isinstance(self.event_status, EventStatus):
            raise TypeError("event_status must be an EventStatus value.")

        successful_statuses = {
            EventStatus.CREATED,
            EventStatus.VALIDATED,
            EventStatus.STORED,
            EventStatus.PROCESSED,
        }
        failed_statuses = {
            EventStatus.FAILED,
            EventStatus.REJECTED,
        }

        if self.success and self.event_status in failed_statuses:
            raise ValueError(
                "Failed event statuses require success=False."
            )

        if not self.success and self.event_status in successful_statuses:
            raise ValueError(
                "Successful event statuses require success=True."
            )

        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        object.__setattr__(self, "event_id", normalized_event_id)
        object.__setattr__(self, "event_type", normalized_event_type)
        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def failed(self) -> bool:
        return not self.success

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_status": self.event_status.value,
            "message": self.message,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def created(
        cls,
        *,
        event_id: str,
        event_type: str,
        message: str = "Event created.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventResult":
        return cls(
            success=True,
            event_id=event_id,
            event_type=event_type,
            event_status=EventStatus.CREATED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def validated(
        cls,
        *,
        event_id: str,
        event_type: str,
        message: str = "Event validated.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventResult":
        return cls(
            success=True,
            event_id=event_id,
            event_type=event_type,
            event_status=EventStatus.VALIDATED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def stored(
        cls,
        *,
        event_id: str,
        event_type: str,
        message: str = "Event stored.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventResult":
        return cls(
            success=True,
            event_id=event_id,
            event_type=event_type,
            event_status=EventStatus.STORED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def processed(
        cls,
        *,
        event_id: str,
        event_type: str,
        message: str = "Event processed.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventResult":
        return cls(
            success=True,
            event_id=event_id,
            event_type=event_type,
            event_status=EventStatus.PROCESSED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def failed_result(
        cls,
        *,
        event_id: str,
        event_type: str,
        message: str = "Event processing failed.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventResult":
        return cls(
            success=False,
            event_id=event_id,
            event_type=event_type,
            event_status=EventStatus.FAILED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def rejected(
        cls,
        *,
        event_id: str,
        event_type: str,
        message: str = "Event rejected.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventResult":
        return cls(
            success=False,
            event_id=event_id,
            event_type=event_type,
            event_status=EventStatus.REJECTED,
            message=message,
            metadata=metadata or {},
        )


__all__ = ["EventResult"]
