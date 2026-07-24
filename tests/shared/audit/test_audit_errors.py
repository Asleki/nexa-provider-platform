"""
============================================================
Nexa Provider Platform
File: tests/shared/audit/test_audit_errors.py
Layer: Audit Unit Tests
Milestone: NPP-M007.1-T1 / M007.4 / M007.5 / M007.6
Revision: v4
============================================================
"""
from __future__ import annotations

import unittest
from types import MappingProxyType

from shared.audit.audit_errors import (
    AuditError,
    AuditIdentifierError,
    AuditMetadataError,
    AuditTimestampError,
    AuditValidationError,
    AuditRepositoryError,
    AuditRepositoryConfigurationError,
    AuditRepositoryOperationError,
    AuditAppendError,
    AuditReadError,
    AuditListError,
    AuditExistsError,
    AuditCountError,
    AuditRecordRepositoryError,
    AuditRecordNotFoundError,
    AuditDuplicateRecordError,
    AuditInvalidRecordError,
    AuditQueryError,
    AuditQueryValidationError,
    AuditQueryServiceConfigurationError,
    AuditQueryExecutionError,
    AuditQueryResultError,
    AuditIntegrityError,
    AuditIntegrityValidationError,
    AuditIntegrityServiceConfigurationError,
    AuditIntegrityExecutionError,
    AuditIntegrityResultError,
)


class AuditErrorTests(unittest.TestCase):

    def test_message_is_normalized(self) -> None:
        error = AuditError("  Failure occurred.  ")
        self.assertEqual(error.message, "Failure occurred.")

    def test_message_must_be_string(self) -> None:
        for value in (None, 123, True, [], {}, object()):
            with self.subTest(message=value):
                with self.assertRaisesRegex(TypeError, "message must be a string"):
                    AuditError(value)  # type: ignore[arg-type]

    def test_message_must_not_be_empty(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(message=value):
                with self.assertRaisesRegex(ValueError, "message must not be empty"):
                    AuditError(value)

    def test_audit_id_validation(self) -> None:
        with self.assertRaisesRegex(TypeError, "audit_id must be a string"):
            AuditError("Failure", audit_id=123)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "audit_id must not be empty when provided"):
            AuditError("Failure", audit_id=" ")

    def test_action_validation(self) -> None:
        with self.assertRaisesRegex(TypeError, "action must be a string"):
            AuditError("Failure", action=123)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "action must not be empty when provided"):
            AuditError("Failure", action=" ")

    def test_metadata_validation(self) -> None:
        for value in (123, "x", [], object()):
            with self.subTest(metadata=value):
                with self.assertRaisesRegex(TypeError, "metadata must be a mapping"):
                    AuditError("Failure", metadata=value)  # type: ignore[arg-type]

    def test_metadata_is_defensively_copied(self) -> None:
        metadata = {"source": "unit"}
        error = AuditError("Failure", metadata=metadata)
        metadata["source"] = "changed"
        self.assertIsInstance(error.metadata, MappingProxyType)
        self.assertEqual(error.metadata["source"], "unit")
        with self.assertRaises(TypeError):
            error.metadata["source"] = "changed"  # type: ignore[index]

    def test_to_dict_returns_plain_dictionary(self) -> None:
        error = AuditValidationError(
            "Validation failed",
            audit_id=" AUD-000001 ",
            action=" CREATE ",
            metadata={"field": "actor_id"},
        )
        self.assertEqual(
            error.to_dict(),
            {
                "error_type": "AuditValidationError",
                "error_code": "NPP-AUDIT-010",
                "message": "Validation failed",
                "audit_id": "AUD-000001",
                "action": "CREATE",
                "metadata": {"field": "actor_id"},
            },
        )

    def test_to_dict_returns_independent_metadata_copy(self) -> None:
        error = AuditError("Failure", metadata={"source": "unit"})
        data = error.to_dict()
        data["metadata"]["source"] = "changed"
        self.assertEqual(error.metadata["source"], "unit")

    def test_error_codes(self) -> None:
        expected_codes = {
            AuditError: "NPP-AUDIT-001",
            AuditValidationError: "NPP-AUDIT-010",
            AuditIdentifierError: "NPP-AUDIT-011",
            AuditTimestampError: "NPP-AUDIT-012",
            AuditMetadataError: "NPP-AUDIT-013",
            AuditRepositoryError: "NPP-AUDIT-100",
            AuditRepositoryConfigurationError: "NPP-AUDIT-101",
            AuditRepositoryOperationError: "NPP-AUDIT-110",
            AuditAppendError: "NPP-AUDIT-111",
            AuditReadError: "NPP-AUDIT-112",
            AuditListError: "NPP-AUDIT-113",
            AuditExistsError: "NPP-AUDIT-114",
            AuditCountError: "NPP-AUDIT-115",
            AuditRecordRepositoryError: "NPP-AUDIT-120",
            AuditRecordNotFoundError: "NPP-AUDIT-121",
            AuditDuplicateRecordError: "NPP-AUDIT-122",
            AuditInvalidRecordError: "NPP-AUDIT-123",
            AuditQueryError: "NPP-AUDIT-200",
            AuditQueryValidationError: "NPP-AUDIT-201",
            AuditQueryServiceConfigurationError: "NPP-AUDIT-202",
            AuditQueryExecutionError: "NPP-AUDIT-203",
            AuditQueryResultError: "NPP-AUDIT-204",
            AuditIntegrityError: "NPP-AUDIT-300",
            AuditIntegrityValidationError: "NPP-AUDIT-301",
            AuditIntegrityServiceConfigurationError: "NPP-AUDIT-302",
            AuditIntegrityExecutionError: "NPP-AUDIT-303",
            AuditIntegrityResultError: "NPP-AUDIT-304",
        }
        for error_class, expected_code in expected_codes.items():
            with self.subTest(error_class=error_class.__name__):
                self.assertEqual(error_class("Failure").error_code, expected_code)

    def test_error_hierarchy(self) -> None:
        subclasses = (
            AuditValidationError, AuditIdentifierError, AuditTimestampError,
            AuditMetadataError, AuditRepositoryError,
            AuditRepositoryConfigurationError, AuditRepositoryOperationError,
            AuditAppendError, AuditReadError, AuditListError, AuditExistsError,
            AuditCountError, AuditRecordRepositoryError,
            AuditRecordNotFoundError, AuditDuplicateRecordError,
            AuditInvalidRecordError, AuditQueryError,
            AuditQueryValidationError, AuditQueryServiceConfigurationError,
            AuditQueryExecutionError, AuditQueryResultError,
            AuditIntegrityError, AuditIntegrityValidationError,
            AuditIntegrityServiceConfigurationError,
            AuditIntegrityExecutionError, AuditIntegrityResultError,
        )
        for error_class in subclasses:
            with self.subTest(error_class=error_class.__name__):
                self.assertIsInstance(error_class("Failure"), AuditError)


if __name__ == "__main__":
    unittest.main()
"""M007.7 additions for tests/shared/audit/test_audit_errors.py.

Append these tests to the existing file after replacing audit_errors.py with v5.
"""
from shared.audit.audit_errors import (
    AuditExportError,
    AuditExportExecutionError,
    AuditExportResultError,
    AuditExportValidationError,
)


def test_audit_export_error_codes_are_stable() -> None:
    assert AuditExportError.error_code == "NPP-AUDIT-400"
    assert AuditExportValidationError.error_code == "NPP-AUDIT-401"
    assert AuditExportExecutionError.error_code == "NPP-AUDIT-402"
    assert AuditExportResultError.error_code == "NPP-AUDIT-403"


def test_audit_export_errors_inherit_export_family() -> None:
    assert issubclass(AuditExportValidationError, AuditExportError)
    assert issubclass(AuditExportExecutionError, AuditExportError)
    assert issubclass(AuditExportResultError, AuditExportError)


"""M007.8 additions for tests/shared/audit/test_audit_errors.py."""
from shared.audit.audit_errors import (
    AuditApiContractError, AuditApiError, AuditApiResultError,
    AuditApiValidationError,
)

def test_m007_8_error_hierarchy_and_codes():
    assert issubclass(AuditApiValidationError, AuditApiError)
    assert issubclass(AuditApiResultError, AuditApiError)
    assert issubclass(AuditApiContractError, AuditApiError)
    assert AuditApiError.error_code == "NPP-AUDIT-500"
    assert AuditApiValidationError.error_code == "NPP-AUDIT-501"
    assert AuditApiResultError.error_code == "NPP-AUDIT-502"
    assert AuditApiContractError.error_code == "NPP-AUDIT-503"
