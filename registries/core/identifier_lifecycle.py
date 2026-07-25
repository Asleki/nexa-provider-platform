"""
============================================================
Nexa Provider Platform
File: registries/core/identifier_lifecycle.py
Layer: Master Registry Foundation
Milestone: M008.2 — Registry Identifier Model
============================================================

Defines the approved persistent lifecycle states for concrete registry
identifier references. This enum is vocabulary only: it does not authorize,
execute, or audit lifecycle transitions. Transition policy belongs to M008.8.

Identifier lifecycle state is independent from storage state. Identifiers are
never silently reused, reassigned, or deleted from permanent history.
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
