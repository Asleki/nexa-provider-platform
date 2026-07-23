"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_event_types.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.2.1 — Audit Event Types
============================================================

Defines the stable event names emitted by the Shared Audit
Infrastructure. These names are audit-domain events and are
separate from the top-level shared.events.EventType.AUDIT
category.
"""

from __future__ import annotations

from enum import Enum


class AuditEventType(str, Enum):
    """Stable audit-domain event names."""

    RECORDED = "audit.recorded"
    VALIDATED = "audit.validated"
    EXPORTED = "audit.exported"
    ARCHIVED = "audit.archived"
    PURGED = "audit.purged"

    def __str__(self) -> str:
        """Return the serialized event name."""

        return self.value


__all__ = ["AuditEventType"]
