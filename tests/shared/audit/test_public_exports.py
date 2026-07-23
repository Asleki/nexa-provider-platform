"""Public export validation through M007.7 Audit Export."""
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
    "AuditQuery", "AuditQueryResult", "AuditQueryService",
    "AuditQueryServiceInterface", "AuditQueryError",
    "AuditQueryValidationError", "AuditQueryServiceConfigurationError",
    "AuditQueryExecutionError", "AuditQueryResultError",
    "AuditIntegrityError", "AuditIntegrityValidationError",
    "AuditIntegrityServiceConfigurationError", "AuditIntegrityExecutionError",
    "AuditIntegrityResultError", "AuditIntegrityFinding",
    "AuditIntegrityResult", "AuditIntegrityStatus",
    "AuditIntegrityValidator", "AuditIntegrityServiceInterface",
    "AuditIntegrityService",
    "AuditExportError", "AuditExportValidationError",
    "AuditExportExecutionError", "AuditExportResultError",
    "AuditExportRequest", "AuditExportResult",
    "AuditExportServiceInterface", "AuditExportService",
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
        "AuditQuery": "shared.audit.audit_query",
        "AuditQueryResult": "shared.audit.audit_query_result",
        "AuditQueryServiceInterface": "shared.audit.audit_query_service_interface",
        "AuditQueryService": "shared.audit.audit_query_service",
        "AuditIntegrityFinding": "shared.audit.audit_integrity_result",
        "AuditIntegrityResult": "shared.audit.audit_integrity_result",
        "AuditIntegrityStatus": "shared.audit.audit_integrity_result",
        "AuditIntegrityValidator": "shared.audit.audit_integrity_validator",
        "AuditIntegrityServiceInterface": "shared.audit.audit_integrity_service_interface",
        "AuditIntegrityService": "shared.audit.audit_integrity_service",
        "AuditExportRequest": "shared.audit.audit_export_request",
        "AuditExportResult": "shared.audit.audit_export_result",
        "AuditExportServiceInterface": "shared.audit.audit_export_service_interface",
        "AuditExportService": "shared.audit.audit_export_service",
    }
    for name, module in expected_modules.items():
        assert getattr(audit_package, name).__module__ == module


def test_star_import_exposes_only_public_names() -> None:
    namespace: dict[str, object] = {}
    exec("from shared.audit import *", namespace)
    assert {name for name in namespace if not name.startswith("__")} == EXPECTED_EXPORTS
"""M007.7 additions for tests/shared/audit/test_public_exports.py.

Append the names below to the existing expected-public-export assertions.
"""
import shared.audit as audit


def test_m007_7_public_exports() -> None:
    expected = {
        "AuditExportError",
        "AuditExportValidationError",
        "AuditExportExecutionError",
        "AuditExportResultError",
        "AuditExportRequest",
        "AuditExportResult",
        "AuditExportServiceInterface",
        "AuditExportService",
    }
    assert expected.issubset(set(audit.__all__))
    for name in expected:
        assert getattr(audit, name) is not None
