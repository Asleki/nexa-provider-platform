"""
============================================================
Nexa Provider Platform
File: shared/events/event_types.py
Layer: Shared Event Infrastructure
Milestone: NPP-M006.1.5 — Event Types
============================================================

Defines the high-level event categories used throughout the
Nexa Provider Platform.

These categories classify events independently from specific
business domains and remain stable as the platform grows.
"""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """Top-level categories for platform events."""

    IDENTITY = "identity"
    PROVIDER = "provider"
    REGISTRY = "registry"
    VERIFICATION = "verification"
    AUDIT = "audit"
    SYSTEM = "system"
    SYNCHRONIZATION = "synchronization"

    def __str__(self) -> str:
        """Return the serialized enum value."""

        return self.value


__all__ = [
    "EventType",
]
