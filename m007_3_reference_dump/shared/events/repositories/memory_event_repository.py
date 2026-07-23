"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/memory_event_repository.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.6 — Memory Event Repository
============================================================

Provides the initial concrete EventEnvelope repository.

The memory repository stores immutable event envelopes in process
memory using deterministic insertion ordering. It is intended for
unit tests, controlled simulations, local development, and early
integration work.

It is not a durable production repository.
"""

from __future__ import annotations

from threading import RLock

from ..event_envelope import EventEnvelope
from .base_event_repository import BaseEventRepository
from .event_repository_errors import (
    EventClearError,
    EventCountError,
    EventDeleteError,
    EventDuplicateError,
    EventExistsError,
    EventListError,
    EventNotFoundError,
    EventReadError,
    EventRepositoryError,
    EventStoreError,
)
from .event_repository_result import EventRepositoryResult
from .event_repository_types import (
    EventRepositoryOperation,
    EventRepositoryType,
)


class MemoryEventRepository(BaseEventRepository):
    """Thread-safe in-memory repository for EventEnvelope objects."""

    def __init__(
        self,
        repository_name: str = "memory_event_repository",
    ) -> None:
        super().__init__(
            repository_name=repository_name,
            repository_type=EventRepositoryType.MEMORY,
        )
        self._events: dict[str, EventEnvelope] = {}
        self._lock = RLock()

    def store(
        self,
        envelope: EventEnvelope,
    ) -> EventRepositoryResult:
        operation = EventRepositoryOperation.STORE

        try:
            validated_envelope = self.validate_envelope(
                envelope,
                operation=operation,
            )
            event_id = validated_envelope.event_id

            with self._lock:
                if event_id in self._events:
                    raise EventDuplicateError(
                        "EventEnvelope with this event_id already exists.",
                        operation=operation,
                        repository=self.repository_name,
                        event_id=event_id,
                        repository_type=self.repository_type,
                    )

                self._events[event_id] = validated_envelope

            return EventRepositoryResult.stored(
                repository=self.repository_name,
                envelope=validated_envelope,
                metadata={"repository_type": self.repository_type},
            )
        except EventRepositoryError:
            raise
        except Exception as exc:
            raise EventStoreError(
                "EventEnvelope could not be stored.",
                operation=operation,
                repository=self.repository_name,
                event_id=(
                    envelope.event_id
                    if isinstance(envelope, EventEnvelope)
                    else None
                ),
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def get(
        self,
        event_id: str,
    ) -> EventRepositoryResult:
        operation = EventRepositoryOperation.READ
        normalized_event_id = self.validate_event_id(
            event_id,
            operation=operation,
        )

        try:
            with self._lock:
                envelope = self._events.get(normalized_event_id)

            if envelope is None:
                raise EventNotFoundError(
                    "EventEnvelope was not found.",
                    operation=operation,
                    repository=self.repository_name,
                    event_id=normalized_event_id,
                    repository_type=self.repository_type,
                )

            return EventRepositoryResult.found(
                repository=self.repository_name,
                envelope=envelope,
                metadata={"repository_type": self.repository_type},
            )
        except EventRepositoryError:
            raise
        except Exception as exc:
            raise EventReadError(
                "EventEnvelope could not be read.",
                operation=operation,
                repository=self.repository_name,
                event_id=normalized_event_id,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def list_all(self) -> EventRepositoryResult:
        operation = EventRepositoryOperation.LIST

        try:
            with self._lock:
                envelopes = tuple(self._events.values())

            return EventRepositoryResult.listed(
                repository=self.repository_name,
                envelopes=envelopes,
                metadata={"repository_type": self.repository_type},
            )
        except EventRepositoryError:
            raise
        except Exception as exc:
            raise EventListError(
                "EventEnvelopes could not be listed.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def exists(
        self,
        event_id: str,
    ) -> EventRepositoryResult:
        operation = EventRepositoryOperation.EXISTS
        normalized_event_id = self.validate_event_id(
            event_id,
            operation=operation,
        )

        try:
            with self._lock:
                event_exists = normalized_event_id in self._events

            return EventRepositoryResult.existence_checked(
                repository=self.repository_name,
                event_id=normalized_event_id,
                exists=event_exists,
                metadata={"repository_type": self.repository_type},
            )
        except EventRepositoryError:
            raise
        except Exception as exc:
            raise EventExistsError(
                "EventEnvelope existence could not be checked.",
                operation=operation,
                repository=self.repository_name,
                event_id=normalized_event_id,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def count(self) -> EventRepositoryResult:
        operation = EventRepositoryOperation.COUNT

        try:
            with self._lock:
                event_count = len(self._events)

            return EventRepositoryResult.counted(
                repository=self.repository_name,
                count=event_count,
                metadata={"repository_type": self.repository_type},
            )
        except EventRepositoryError:
            raise
        except Exception as exc:
            raise EventCountError(
                "EventEnvelopes could not be counted.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def delete(
        self,
        event_id: str,
    ) -> EventRepositoryResult:
        operation = EventRepositoryOperation.DELETE
        normalized_event_id = self.validate_event_id(
            event_id,
            operation=operation,
        )

        try:
            with self._lock:
                if normalized_event_id not in self._events:
                    raise EventNotFoundError(
                        "EventEnvelope was not found.",
                        operation=operation,
                        repository=self.repository_name,
                        event_id=normalized_event_id,
                        repository_type=self.repository_type,
                    )

                del self._events[normalized_event_id]

            return EventRepositoryResult.deleted(
                repository=self.repository_name,
                event_id=normalized_event_id,
                metadata={"repository_type": self.repository_type},
            )
        except EventRepositoryError:
            raise
        except Exception as exc:
            raise EventDeleteError(
                "EventEnvelope could not be deleted.",
                operation=operation,
                repository=self.repository_name,
                event_id=normalized_event_id,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def clear(self) -> EventRepositoryResult:
        operation = EventRepositoryOperation.CLEAR

        try:
            with self._lock:
                events_removed = len(self._events)
                self._events.clear()

            return EventRepositoryResult.cleared(
                repository=self.repository_name,
                events_removed=events_removed,
                metadata={"repository_type": self.repository_type},
            )
        except EventRepositoryError:
            raise
        except Exception as exc:
            raise EventClearError(
                "Event repository could not be cleared.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc


__all__ = [
    "MemoryEventRepository",
]
