from __future__ import annotations

from inspect import isabstract

from shared.audit.audit_integrity_service_interface import (
    AuditIntegrityServiceInterface,
)


def test_interface_is_abstract() -> None:
    assert isabstract(AuditIntegrityServiceInterface)


def test_interface_declares_both_validation_operations() -> None:
    assert "validate_record" in AuditIntegrityServiceInterface.__abstractmethods__
    assert "validate_records" in AuditIntegrityServiceInterface.__abstractmethods__
