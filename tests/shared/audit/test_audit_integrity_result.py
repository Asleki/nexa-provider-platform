from __future__ import annotations

import pytest

from shared.audit.audit_errors import AuditIntegrityResultError
from shared.audit.audit_integrity_result import (
    AuditIntegrityFinding,
    AuditIntegrityResult,
    AuditIntegrityStatus,
)


def test_valid_result_has_no_findings() -> None:
    result = AuditIntegrityResult(AuditIntegrityStatus.VALID, 2)
    assert result.is_valid
    assert not result.is_invalid
    assert result.records_checked == 2


def test_invalid_result_requires_findings() -> None:
    finding = AuditIntegrityFinding("DUPLICATE_AUDIT_ID", "duplicate", "A-1", 1)
    result = AuditIntegrityResult(
        AuditIntegrityStatus.INVALID, 2, (finding,)
    )
    assert result.is_invalid
    assert result.findings == (finding,)


def test_status_and_findings_must_be_consistent() -> None:
    with pytest.raises(AuditIntegrityResultError):
        AuditIntegrityResult(AuditIntegrityStatus.INVALID, 0)
