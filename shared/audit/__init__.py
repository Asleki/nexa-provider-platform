"""
============================================================
Nexa Provider Platform
File: shared/audit/__init__.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.3 — Actor and Source Metadata
Revision: v3
============================================================

Defines the stable public import surface for the Shared Audit
Infrastructure. Domain contracts from M007.1 and audit-event
contracts from M007.2 are re-exported from this package without
introducing repository, storage, or runtime-specific behavior.
"""

from __future__ import annotations

from .audit_action import AuditAction
from .audit_actor import AuditActor
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
from .audit_metadata import AuditMetadata
from .audit_outcome import AuditOutcome
from .audit_source import AuditSource
from .audit_record import AuditRecord


__all__ = [
    "AuditAction",
    "AuditActor",
    "AuditError",
    "AuditEvent",
    "AuditEventResult",
    "AuditEventType",
    "AuditIdentifierError",
    "AuditMetadata",
    "AuditMetadataError",
    "AuditOutcome",
    "AuditRecord",
    "AuditSource",
    "AuditTimestampError",
    "AuditValidationError",
]
