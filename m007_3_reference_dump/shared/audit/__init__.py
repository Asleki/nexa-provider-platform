"""
============================================================
Nexa Provider Platform
File: shared/audit/__init__.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.2 — Audit Event Model
Revision: v2
============================================================

Defines the stable public import surface for the Shared Audit
Infrastructure. Domain contracts from M007.1 and audit-event
contracts from M007.2 are re-exported from this package without
introducing repository, storage, or runtime-specific behavior.
"""

from __future__ import annotations

from .audit_action import AuditAction
from .audit_errors import (
    AuditError,
    AuditIdentifierError,
    AuditMetadataError,
    AuditTimestampError,
    AuditValidationError,
)
from .audit_event import AuditEvent
from .audit_event_result import AuditEventResult
from .audit_event_types import AuditEventType
from .audit_outcome import AuditOutcome
from .audit_record import AuditRecord


__all__ = [
    "AuditAction",
    "AuditError",
    "AuditEvent",
    "AuditEventResult",
    "AuditEventType",
    "AuditIdentifierError",
    "AuditMetadataError",
    "AuditOutcome",
    "AuditRecord",
    "AuditTimestampError",
    "AuditValidationError",
]
