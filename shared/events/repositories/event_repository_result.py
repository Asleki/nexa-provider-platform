"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/event_repository_result.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.3 — Event Repository Result
============================================================

Defines the standardized result returned by successful
event-repository operations.

EventRepositoryResult provides a predictable, immutable
contract to higher layers while event-repository exceptions
represent failed operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from ..event_envelope import EventEnvelope
from .event_repository_types import EventRepositoryOperation


def _freeze_envelopes(
    envelopes: tuple[EventEnvelope, ...],
) -> tuple[EventEnvelope, ...]:
    """
    Validate and return an immutable tuple of EventEnvelope objects.
    """

    normalized = tuple(envelopes)

    for envelope in normalized:
        if not isinstance(envelope, EventEnvelope):
            raise TypeError(
                "envelopes must contain only EventEnvelope objects."
            )

    return normalized


@dataclass(frozen=True, slots=True)
class EventRepositoryResult:
    """
    Standard result returned by successful event-repository operations.

    Attributes
    ----------
    success:
        Indicates whether the repository operation succeeded.

    operation:
        Event-repository operation that produced this result.

    repository:
        Logical event-repository name.

    event_id:
        Immutable identifier of the affected or retrieved event.

    envelope:
        Single EventEnvelope returned by store or read operations.

    envelopes:
        Collection returned by list operations.

    events_affected:
        Number of event records affected or represented.

    message:
        Human-readable result description.

    metadata:
        Additional implementation-neutral context.
    """

    success: bool
    operation: EventRepositoryOperation
    repository: str
    event_id: str | None = None
    envelope: EventEnvelope | None = None
    envelopes: tuple[EventEnvelope, ...] = ()
    events_affected: int = 0
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate, normalize, and freeze result state."""

        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(
            self.operation,
            EventRepositoryOperation,
        ):
            raise TypeError(
                "operation must be an EventRepositoryOperation."
            )

        if not isinstance(self.repository, str):
            raise TypeError("repository must be a string.")

        normalized_repository = self.repository.strip()

        if not normalized_repository:
            raise ValueError("repository must not be empty.")

        if self.event_id is not None:
            if not isinstance(self.event_id, str):
                raise TypeError(
                    "event_id must be a string when provided."
                )

            normalized_event_id = self.event_id.strip()

            if not normalized_event_id:
                raise ValueError(
                    "event_id must not be empty when provided."
                )

            object.__setattr__(
                self,
                "event_id",
                normalized_event_id,
            )

        if self.envelope is not None:
            if not isinstance(self.envelope, EventEnvelope):
                raise TypeError(
                    "envelope must be an EventEnvelope when provided."
                )

            if (
                self.event_id is not None
                and self.envelope.event_id != self.event_id
            ):
                raise ValueError(
                    "event_id must match envelope.event_id."
                )

        if not isinstance(self.events_affected, int):
            raise TypeError("events_affected must be an integer.")

        if isinstance(self.events_affected, bool):
            raise TypeError("events_affected must be an integer.")

        if self.events_affected < 0:
            raise ValueError(
                "events_affected must not be negative."
            )

        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        object.__setattr__(
            self,
            "repository",
            normalized_repository,
        )
        object.__setattr__(
            self,
            "envelopes",
            _freeze_envelopes(tuple(self.envelopes)),
        )
        object.__setattr__(
            self,
            "message",
            self.message.strip(),
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def failed(self) -> bool:
        """Return True when the operation failed."""

        return not self.success

    @property
    def count(self) -> int:
        """
        Return the number of events represented by this result.

        For list operations this is the number of returned envelopes.
        For other operations this is events_affected.
        """

        if self.operation is EventRepositoryOperation.LIST:
            return len(self.envelopes)

        return self.events_affected

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result into a plain dictionary."""

        return {
            "success": self.success,
            "operation": self.operation.value,
            "repository": self.repository,
            "event_id": self.event_id,
            "envelope": (
                self.envelope.to_dict()
                if self.envelope is not None
                else None
            ),
            "envelopes": [
                envelope.to_dict()
                for envelope in self.envelopes
            ],
            "events_affected": self.events_affected,
            "message": self.message,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def stored(
        cls,
        *,
        repository: str,
        envelope: EventEnvelope,
        message: str = "Event envelope stored.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventRepositoryResult":
        """Create a successful store-operation result."""

        return cls(
            success=True,
            operation=EventRepositoryOperation.STORE,
            repository=repository,
            event_id=envelope.event_id,
            envelope=envelope,
            events_affected=1,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def found(
        cls,
        *,
        repository: str,
        envelope: EventEnvelope,
        message: str = "Event envelope found.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventRepositoryResult":
        """Create a successful read-operation result."""

        return cls(
            success=True,
            operation=EventRepositoryOperation.READ,
            repository=repository,
            event_id=envelope.event_id,
            envelope=envelope,
            events_affected=1,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def deleted(
        cls,
        *,
        repository: str,
        event_id: str,
        message: str = "Event envelope deleted.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventRepositoryResult":
        """Create a successful delete-operation result."""

        return cls(
            success=True,
            operation=EventRepositoryOperation.DELETE,
            repository=repository,
            event_id=event_id,
            events_affected=1,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def listed(
        cls,
        *,
        repository: str,
        envelopes: tuple[EventEnvelope, ...],
        message: str = "Event envelopes listed.",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventRepositoryResult":
        """Create a successful list-operation result."""

        normalized_envelopes = tuple(envelopes)

        return cls(
            success=True,
            operation=EventRepositoryOperation.LIST,
            repository=repository,
            envelopes=normalized_envelopes,
            events_affected=len(normalized_envelopes),
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def existence_checked(
        cls,
        *,
        repository: str,
        event_id: str,
        exists: bool,
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventRepositoryResult":
        """Create a successful exists-operation result."""

        if not isinstance(exists, bool):
            raise TypeError("exists must be a boolean.")

        combined_metadata = dict(metadata or {})
        combined_metadata["exists"] = exists

        return cls(
            success=True,
            operation=EventRepositoryOperation.EXISTS,
            repository=repository,
            event_id=event_id,
            events_affected=1 if exists else 0,
            message=(
                "Event envelope exists."
                if exists
                else "Event envelope does not exist."
            ),
            metadata=combined_metadata,
        )

    @classmethod
    def counted(
        cls,
        *,
        repository: str,
        count: int,
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventRepositoryResult":
        """Create a successful count-operation result."""

        if not isinstance(count, int) or isinstance(count, bool):
            raise TypeError("count must be an integer.")

        if count < 0:
            raise ValueError("count must not be negative.")

        combined_metadata = dict(metadata or {})
        combined_metadata["count"] = count

        return cls(
            success=True,
            operation=EventRepositoryOperation.COUNT,
            repository=repository,
            events_affected=count,
            message="Event envelopes counted.",
            metadata=combined_metadata,
        )

    @classmethod
    def cleared(
        cls,
        *,
        repository: str,
        events_removed: int,
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventRepositoryResult":
        """Create a successful clear-operation result."""

        if (
            not isinstance(events_removed, int)
            or isinstance(events_removed, bool)
        ):
            raise TypeError("events_removed must be an integer.")

        if events_removed < 0:
            raise ValueError(
                "events_removed must not be negative."
            )

        combined_metadata = dict(metadata or {})
        combined_metadata["events_removed"] = events_removed

        return cls(
            success=True,
            operation=EventRepositoryOperation.CLEAR,
            repository=repository,
            events_affected=events_removed,
            message="Event repository cleared.",
            metadata=combined_metadata,
        )


__all__ = [
    "EventRepositoryResult",
]
