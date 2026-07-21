"""
============================================================
Nexa Provider Platform
File: shared/events/event_envelope.py
Layer: Shared Event Engine
Milestone: NPP-M006.2.3 — Event Envelope
============================================================

Defines the immutable container passed into the Event Engine.

An EventEnvelope combines an EventInterface instance with the
EventContext describing the environment in which the event
is processed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .event_context import EventContext
from .event_interface import EventInterface


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """
    Immutable processing envelope.

    Wraps an event together with its execution context.
    """

    event: EventInterface
    context: EventContext

    def __post_init__(self) -> None:
        if not isinstance(self.event, EventInterface):
            raise TypeError("event must implement EventInterface.")

        if not isinstance(self.context, EventContext):
            raise TypeError("context must be an EventContext.")

    @property
    def event_id(self) -> str:
        return self.event.event_id

    @property
    def event_type(self) -> str:
        return self.event.event_type

    def to_dict(self) -> dict:
        return {
            "event": self.event.to_dict(),
            "context": self.context.to_dict(),
        }


__all__ = [
    "EventEnvelope",
]
