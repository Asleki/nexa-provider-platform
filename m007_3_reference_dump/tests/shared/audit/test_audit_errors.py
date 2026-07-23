"""
============================================================
Nexa Provider Platform
File: tests/unit/audit/test_audit_errors.py
Layer: Audit Unit Tests
Milestone: NPP-M007.1-T1 — Audit Errors Tests
============================================================

Verifies the AuditError hierarchy, validation, normalization,
immutability, metadata handling, error codes, and serialization.
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
)


class AuditErrorTests(unittest.TestCase):

    def test_message_is_normalized(self) -> None:
        error = AuditError("  Failure occurred.  ")
        self.assertEqual(error.message, "Failure occurred.")

    def test_message_must_be_string(self) -> None:
        for value in (None, 123, True, [], {}, object()):
            with self.subTest(message=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "message must be a string",
                ):
                    AuditError(value)  # type: ignore[arg-type]

    def test_message_must_not_be_empty(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(message=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "message must not be empty",
                ):
                    AuditError(value)

    def test_audit_id_validation(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "audit_id must be a string",
        ):
            AuditError(
                "Failure",
                audit_id=123,  # type: ignore[arg-type]
            )

        with self.assertRaisesRegex(
            ValueError,
            "audit_id must not be empty when provided",
        ):
            AuditError("Failure", audit_id=" ")

    def test_action_validation(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "action must be a string",
        ):
            AuditError(
                "Failure",
                action=123,  # type: ignore[arg-type]
            )

        with self.assertRaisesRegex(
            ValueError,
            "action must not be empty when provided",
        ):
            AuditError("Failure", action=" ")

    def test_metadata_validation(self) -> None:
        for value in (123, "x", [], object()):
            with self.subTest(metadata=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "metadata must be a mapping",
                ):
                    AuditError(
                        "Failure",
                        metadata=value,  # type: ignore[arg-type]
                    )

    def test_metadata_is_defensively_copied(self) -> None:
        metadata = {"source": "unit"}

        error = AuditError(
            "Failure",
            metadata=metadata,
        )

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
        error = AuditError(
            "Failure",
            metadata={"source": "unit"},
        )

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
        }

        for error_class, expected_code in expected_codes.items():
            with self.subTest(error_class=error_class.__name__):
                error = error_class("Failure")
                self.assertEqual(error.error_code, expected_code)

    def test_error_hierarchy(self) -> None:
        subclasses = (
            AuditValidationError,
            AuditIdentifierError,
            AuditTimestampError,
            AuditMetadataError,
        )

        for error_class in subclasses:
            with self.subTest(error_class=error_class.__name__):
                instance = error_class("Failure")
                self.assertIsInstance(instance, AuditError)


if __name__ == "__main__":
    unittest.main()
