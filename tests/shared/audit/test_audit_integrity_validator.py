from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from shared.audit.audit_action import AuditAction
from shared.audit.audit_errors import AuditIntegrityValidationError
from shared.audit.audit_integrity_result import AuditIntegrityStatus
from shared.audit.audit_integrity_validator import AuditIntegrityValidator
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord


def make_record(audit_id: str, when: datetime) -> AuditRecord:
    return AuditRecord(
        audit_id=audit_id,
        version=1,
        recorded_at=when,
        action=next(iter(AuditAction)),
        outcome=next(iter(AuditOutcome)),
        actor_id="actor-1",
        actor_type="operator",
        target_namespace="provider",
        target_type="citizen",
        target_id="target-1",
        runtime_id="runtime-1",
        runtime_mode="simulation",
        source="test",
    )


def test_valid_chronological_sequence() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = AuditIntegrityValidator().validate_records(
        (make_record("A-1", start), make_record("A-2", start + timedelta(seconds=1)))
    )
    assert result.status is AuditIntegrityStatus.VALID
    assert result.records_checked == 2


def test_duplicate_and_out_of_order_are_reported() -> None:
    later = datetime(2026, 1, 2, tzinfo=timezone.utc)
    earlier = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = AuditIntegrityValidator().validate_records(
        (make_record("A-1", later), make_record("A-1", earlier))
    )
    assert result.status is AuditIntegrityStatus.INVALID
    assert {finding.code for finding in result.findings} == {
        "DUPLICATE_AUDIT_ID",
        "NON_CHRONOLOGICAL_ORDER",
    }


def test_rejects_non_records() -> None:
    with pytest.raises(AuditIntegrityValidationError):
        AuditIntegrityValidator().validate_records(("not-a-record",))
