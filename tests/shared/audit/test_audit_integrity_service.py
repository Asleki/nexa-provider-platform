from __future__ import annotations

from datetime import datetime, timezone

import pytest

from shared.audit.audit_action import AuditAction
from shared.audit.audit_errors import AuditIntegrityServiceConfigurationError
from shared.audit.audit_integrity_service import AuditIntegrityService
from shared.audit.audit_integrity_validator import AuditIntegrityValidator
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord


def make_record() -> AuditRecord:
    return AuditRecord(
        audit_id="A-1",
        version=1,
        recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
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


def test_service_uses_default_validator() -> None:
    service = AuditIntegrityService()
    assert isinstance(service.validator, AuditIntegrityValidator)
    assert service.validate_record(make_record()).is_valid


def test_service_accepts_validator_dependency() -> None:
    validator = AuditIntegrityValidator()
    assert AuditIntegrityService(validator).validator is validator


def test_service_rejects_invalid_validator() -> None:
    with pytest.raises(AuditIntegrityServiceConfigurationError):
        AuditIntegrityService(object())
