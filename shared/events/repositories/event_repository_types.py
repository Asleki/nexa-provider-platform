"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/event_repository_types.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.2 — Event Repository Types
============================================================

Defines stable event-repository operation and implementation
type identifiers.

These enums keep higher layers independent from concrete
storage technologies while preserving event-specific
repository semantics.
"""

from __future__ import annotations

from enum import Enum


class EventRepositoryOperation(str, Enum):
    """
    Supported event-repository operations.

    Event repositories persist immutable EventEnvelope objects.
    Therefore, no update operation is defined.
    """

    STORE = "store"
    READ = "read"
    DELETE = "delete"
    LIST = "list"
    EXISTS = "exists"
    COUNT = "count"
    CLEAR = "clear"


class EventRepositoryType(str, Enum):
    """
    Supported event-repository implementation types.

    MEMORY is the initial implementation used for deterministic
    tests, controlled simulations, and early integration work.

    Additional implementations may be added in later milestones
    without changing Event Engine or Provider Service contracts.
    """

    MEMORY = "memory"


__all__ = [
    "EventRepositoryOperation",
    "EventRepositoryType",
]
