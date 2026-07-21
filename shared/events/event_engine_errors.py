"""
============================================================
Nexa Provider Platform
File: shared/events/event_engine_errors.py
Layer: Shared Event Engine
Milestone: NPP-M006.2.4 — Event Engine Errors
============================================================

Defines exceptions specific to the Event Engine.

These errors describe failures in handler registration,
resolution, and execution. General event validation and
serialization errors remain in event_errors.py.
"""

from __future__ import annotations

from .event_errors import EventProcessingError


class EventEngineError(EventProcessingError):
    """Base exception for Event Engine failures."""


class HandlerNotRegisteredError(EventEngineError):
    """Raised when no handler is registered for an event."""


class DuplicateHandlerRegistrationError(EventEngineError):
    """Raised when attempting to register the same handler twice."""


class InvalidHandlerError(EventEngineError):
    """Raised when an object does not satisfy the EventHandler contract."""


class HandlerExecutionError(EventEngineError):
    """Raised when a registered handler fails during execution."""


__all__ = [
    "DuplicateHandlerRegistrationError",
    "EventEngineError",
    "HandlerExecutionError",
    "HandlerNotRegisteredError",
    "InvalidHandlerError",
]
