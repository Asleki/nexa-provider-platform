"""
============================================================
Nexa Provider Platform
File: registries/core/registry_status.py
Layer: Master Registry Foundation
Milestone: NPP-M006.2 — Registry Package Skeleton
============================================================

Defines lifecycle statuses for registry definitions.

Registry status describes whether a registry definition may be
used for new operational activity. Historical records remain
auditable even when a registry is suspended or retired.
"""

from __future__ import annotations

from enum import Enum


class RegistryStatus(str, Enum):
    """Supported registry-definition lifecycle statuses."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


__all__ = [
    "RegistryStatus",
]
