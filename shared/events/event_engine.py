"""
============================================================
Nexa Provider Platform
File: shared/events/event_engine.py
Layer: Shared Event Engine
Milestone: NPP-M006.2.5 — Event Engine
============================================================

Coordinates validation, handler resolution and execution for
platform events.

The engine is infrastructure-only and intentionally contains
no repository, transport, persistence or provider logic.
"""

from __future__ import annotations

from typing import Dict

from .event_envelope import EventEnvelope
from .event_engine_errors import (
    DuplicateHandlerRegistrationError,
    HandlerExecutionError,
    HandlerNotRegisteredError,
    InvalidHandlerError,
)
from .event_handler import EventHandler


class EventEngine:
    """
    Central event execution coordinator.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, EventHandler] = {}

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def register_handler(self, handler: EventHandler) -> None:
        if not isinstance(handler, EventHandler):
            raise InvalidHandlerError(
                "Handler must implement EventHandler."
            )

        event_type = handler.event_type.strip()

        if event_type in self._handlers:
            raise DuplicateHandlerRegistrationError(
                f"Handler already registered for '{event_type}'."
            )

        self._handlers[event_type] = handler

    def unregister_handler(self, event_type: str) -> None:
        self._handlers.pop(event_type.strip(), None)

    def has_handler(self, event_type: str) -> bool:
        return event_type.strip() in self._handlers

    def resolve_handler(self, event_type: str) -> EventHandler:
        try:
            return self._handlers[event_type.strip()]
        except KeyError as exc:
            raise HandlerNotRegisteredError(
                f"No handler registered for '{event_type}'."
            ) from exc

    def process(self, envelope: EventEnvelope):
        event = envelope.event
        event.validate()

        handler = self.resolve_handler(event.event_type)

        if not handler.can_handle(event):
            raise HandlerNotRegisteredError(
                f"Registered handler rejected '{event.event_type}'."
            )

        try:
            return handler.handle(event)
        except Exception as exc:
            raise HandlerExecutionError(
                f"Handler execution failed for '{event.event_type}'."
            ) from exc


__all__ = [
    "EventEngine",
]
