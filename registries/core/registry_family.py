"""
============================================================
Nexa Provider Platform
File: registries/core/registry_family.py
Layer: Master Registry Foundation
Milestone: NPP-M006.2 — Registry Package Skeleton
============================================================

Defines the approved high-level registry families used by the
Nexa Provider Platform.

Registry families classify registries without transferring
ownership between domains or coupling registry definitions to a
particular storage implementation.
"""

from __future__ import annotations

from enum import Enum


class RegistryFamily(str, Enum):
    """Approved Master Registry families."""

    CORE_INFRASTRUCTURE = "core_infrastructure"
    NEXA_ECOSYSTEM = "nexa_ecosystem"
    SHARED_INFRASTRUCTURE = "shared_infrastructure"


__all__ = [
    "RegistryFamily",
]
