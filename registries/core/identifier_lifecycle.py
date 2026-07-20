"""
============================================================
Nexa Provider Platform
File: registries/core/identifier_lifecycle.py
Layer: Master Registry Foundation
Milestone: NPP-M006.2 — Registry Package Skeleton
============================================================

Defines the approved lifecycle states for registry identifiers.

Identifier lifecycle state is independent from storage state.
Identifiers are never silently reused, reassigned, or deleted from
their permanent audit history.
"""

from __future__ import annotations

from enum import Enum


class IdentifierLifecycle(str, Enum):
    """Supported identifier lifecycle states."""

    REQUESTED = "requested"
    VALIDATED = "validated"
    ISSUED = "issued"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


__all__ = [
    "IdentifierLifecycle",
]
