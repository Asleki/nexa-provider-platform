"""Public export validation for M007.4 Audit Repository."""

from __future__ import annotations

import shared.audit as audit_package

EXPECTED_EXPORTS = {
    "AuditAction", "AuditActor", "AuditAppendError", "AuditCountError",
    "AuditDuplicateRecordError", "AuditError", "AuditEvent",
    "AuditEventResult", "AuditEventType", "AuditExistsError",
    "AuditIdentifierError", "AuditInvalidRecordError", "AuditListError",
    "AuditMetadata", "AuditMetadataError", "AuditOutcome", "AuditReadError",
    "AuditRecord", "AuditRecordNotFoundError", "AuditRecordRepositoryError",
    "AuditRepositoryConfigurationError", "AuditRepositoryError",
    "AuditRepositoryInterface", "AuditRepositoryOperation",
    "AuditRepositoryOperationError", "AuditRepositoryResult",
    "AuditRepositoryType", "AuditSource", "AuditTimestampError",
    "AuditValidationError", "BaseAuditRepository", "MemoryAuditRepository",
}


def test_package_all_contains_expected_exports() -> None:
    assert set(audit_package.__all__) == EXPECTED_EXPORTS


def test_package_all_contains_only_unique_strings() -> None:
    assert all(isinstance(name, str) for name in audit_package.__all__)
    assert len(audit_package.__all__) == len(set(audit_package.__all__))


def test_package_exports_are_available() -> None:
    for name in EXPECTED_EXPORTS:
        assert hasattr(audit_package, name)


def test_package_exports_have_canonical_modules() -> None:
    expected_modules = {
        "AuditRepositoryOperation": "shared.audit.audit_repository_types",
        "AuditRepositoryType": "shared.audit.audit_repository_types",
        "AuditRepositoryResult": "shared.audit.audit_repository_result",
        "AuditRepositoryInterface": "shared.audit.audit_repository_interface",
        "BaseAuditRepository": "shared.audit.base_audit_repository",
        "MemoryAuditRepository": "shared.audit.memory_audit_repository",
    }
    for name, module in expected_modules.items():
        assert getattr(audit_package, name).__module__ == module


def test_star_import_exposes_only_public_names() -> None:
    namespace: dict[str, object] = {}
    exec("from shared.audit import *", namespace)
    assert {name for name in namespace if not name.startswith("__")} == EXPECTED_EXPORTS
