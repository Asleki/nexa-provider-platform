"""
============================================================
Nexa Provider Platform
File: registries/events/registry_event_type.py
Layer: Master Registry Foundation
Milestone: NPP-M008.10 — Registry Events
============================================================

Canonical business-fact event names emitted by the master-registry domain.
These values extend the shared M006 event infrastructure and do not define a
second event bus.
============================================================
"""

from __future__ import annotations

from enum import Enum


class RegistryEventType(str, Enum):
    """Supported immutable registry-domain business facts."""

    REGISTRY_REGISTERED = "registry.registered"
    REGISTRY_REPLACED = "registry.replaced"
    REGISTRY_REMOVED = "registry.removed"
    REGISTRY_STATUS_CHANGED = "registry.status_changed"

    def __str__(self) -> str:
        return self.value

    @property
    def action(self) -> str:
        """Return the terminal action segment used by routing and reporting."""

        return self.value.rsplit(".", 1)[-1]


__all__ = ["RegistryEventType"]
