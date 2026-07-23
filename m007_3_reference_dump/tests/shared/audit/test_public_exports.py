"""
============================================================
Nexa Provider Platform
File: tests/shared/audit/test_public_exports.py
Layer: Shared Audit Infrastructure Tests
Milestone: NPP-M007.2 — Audit Event Model
Revision: v2
============================================================

Verifies that shared.audit exposes the complete, stable public API
for the M007.1 audit contracts and the M007.2 audit-event model.
"""

from __future__ import annotations

import shared.audit as audit_package
from shared.audit import (
    AuditAction,
    AuditError,
    AuditEvent,
    AuditEventResult,
    AuditEventType,
    AuditIdentifierError,
    AuditMetadataError,
    AuditOutcome,
    AuditRecord,
    AuditTimestampError,
    AuditValidationError,
)
from shared.audit.audit_action import AuditAction as CanonicalAuditAction
from shared.audit.audit_errors import (
    AuditError as CanonicalAuditError,
    AuditIdentifierError as CanonicalAuditIdentifierError,
    AuditMetadataError as CanonicalAuditMetadataError,
    AuditTimestampError as CanonicalAuditTimestampError,
    AuditValidationError as CanonicalAuditValidationError,
)
from shared.audit.audit_event import AuditEvent as CanonicalAuditEvent
from shared.audit.audit_event_result import (
    AuditEventResult as CanonicalAuditEventResult,
)
from shared.audit.audit_event_types import (
    AuditEventType as CanonicalAuditEventType,
)
from shared.audit.audit_outcome import AuditOutcome as CanonicalAuditOutcome
from shared.audit.audit_record import AuditRecord as CanonicalAuditRecord


EXPECTED_EXPORTS = {
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
}


def test_package_all_contains_expected_exports() -> None:
    assert set(audit_package.__all__) == EXPECTED_EXPORTS


def test_package_all_contains_only_unique_strings() -> None:
    assert all(isinstance(name, str) for name in audit_package.__all__)
    assert len(audit_package.__all__) == len(set(audit_package.__all__))


def test_package_exports_are_available() -> None:
    for name in EXPECTED_EXPORTS:
        assert hasattr(audit_package, name)


def test_package_exports_have_canonical_identity() -> None:
    assert AuditAction is CanonicalAuditAction
    assert AuditError is CanonicalAuditError
    assert AuditEvent is CanonicalAuditEvent
    assert AuditEventResult is CanonicalAuditEventResult
    assert AuditEventType is CanonicalAuditEventType
    assert AuditIdentifierError is CanonicalAuditIdentifierError
    assert AuditMetadataError is CanonicalAuditMetadataError
    assert AuditOutcome is CanonicalAuditOutcome
    assert AuditRecord is CanonicalAuditRecord
    assert AuditTimestampError is CanonicalAuditTimestampError
    assert AuditValidationError is CanonicalAuditValidationError


def test_star_import_exposes_only_public_names() -> None:
    namespace: dict[str, object] = {}
    exec("from shared.audit import *", namespace)

    public_names = {
        name for name in namespace if not name.startswith("__")
    }
    assert public_names == EXPECTED_EXPORTS
