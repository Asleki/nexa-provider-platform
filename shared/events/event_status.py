"""
============================================================
Nexa Provider Platform
File: shared/events/event_status.py
Layer: Shared Event Infrastructure
Milestone: NPP-M006.1.6 — Event Status
============================================================

Defines the lifecycle states an event may progress through.

EventStatus is used by EventResult and other infrastructure
components to consistently represent processing state.
"""

from __future__ import annotations

from enum import Enum


class EventStatus(str, Enum):
    """Lifecycle states for platform events."""

    CREATED = "created"
    VALIDATED = "validated"
    STORED = "stored"
    PROCESSED = "processed"
    FAILED = "failed"
    REJECTED = "rejected"

    def __str__(self) -> str:
        """Return the serialized enum value."""
        return self.value

    @property
    def is_success(self) -> bool:
        """Return True if the status represents successful progress."""
        return self in {
            EventStatus.CREATED,
            EventStatus.VALIDATED,
            EventStatus.STORED,
            EventStatus.PROCESSED,
        }

    @property
    def is_terminal(self) -> bool:
        """Return True if the status is terminal."""
        return self in {
            EventStatus.PROCESSED,
            EventStatus.FAILED,
            EventStatus.REJECTED,
        }


__all__ = [
    "EventStatus",
]
