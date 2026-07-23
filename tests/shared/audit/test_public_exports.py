"""
============================================================
Nexa Provider Platform
File: tests/shared/audit/test_public_exports.py
Layer: Shared Audit Tests
Milestone: NPP-M007.1-T5 — Audit Public Export Tests
============================================================

Verifies that shared.audit exposes the approved public API
through direct package imports and __all__.
"""

from __future__ import annotations

import unittest

import shared.audit as audit
from shared.audit import (
    AuditAction,
    AuditError,
    AuditIdentifierError,
    AuditMetadataError,
    AuditOutcome,
    AuditRecord,
    AuditTimestampError,
    AuditValidationError,
)
from shared.audit.audit_action import AuditAction as DirectAuditAction
from shared.audit.audit_errors import (
    AuditError as DirectAuditError,
    AuditIdentifierError as DirectAuditIdentifierError,
    AuditMetadataError as DirectAuditMetadataError,
    AuditTimestampError as DirectAuditTimestampError,
    AuditValidationError as DirectAuditValidationError,
)
from shared.audit.audit_outcome import AuditOutcome as DirectAuditOutcome
from shared.audit.audit_record import AuditRecord as DirectAuditRecord


class AuditPublicExportsTests(unittest.TestCase):

    def test_all_contains_expected_public_symbols(self) -> None:
        self.assertEqual(
            audit.__all__,
            [
                "AuditAction",
                "AuditError",
                "AuditIdentifierError",
                "AuditMetadataError",
                "AuditOutcome",
                "AuditRecord",
                "AuditTimestampError",
                "AuditValidationError",
            ],
        )

    def test_package_exports_expected_symbols(self) -> None:
        expected_exports = {
            "AuditAction": DirectAuditAction,
            "AuditError": DirectAuditError,
            "AuditIdentifierError": DirectAuditIdentifierError,
            "AuditMetadataError": DirectAuditMetadataError,
            "AuditOutcome": DirectAuditOutcome,
            "AuditRecord": DirectAuditRecord,
            "AuditTimestampError": DirectAuditTimestampError,
            "AuditValidationError": DirectAuditValidationError,
        }

        for name, expected_object in expected_exports.items():
            with self.subTest(name=name):
                self.assertTrue(hasattr(audit, name))
                self.assertIs(getattr(audit, name), expected_object)

    def test_from_package_imports_resolve_to_canonical_objects(self) -> None:
        imported_objects = {
            "AuditAction": AuditAction,
            "AuditError": AuditError,
            "AuditIdentifierError": AuditIdentifierError,
            "AuditMetadataError": AuditMetadataError,
            "AuditOutcome": AuditOutcome,
            "AuditRecord": AuditRecord,
            "AuditTimestampError": AuditTimestampError,
            "AuditValidationError": AuditValidationError,
        }
        canonical_objects = {
            "AuditAction": DirectAuditAction,
            "AuditError": DirectAuditError,
            "AuditIdentifierError": DirectAuditIdentifierError,
            "AuditMetadataError": DirectAuditMetadataError,
            "AuditOutcome": DirectAuditOutcome,
            "AuditRecord": DirectAuditRecord,
            "AuditTimestampError": DirectAuditTimestampError,
            "AuditValidationError": DirectAuditValidationError,
        }

        for name, imported_object in imported_objects.items():
            with self.subTest(name=name):
                self.assertIs(imported_object, canonical_objects[name])

    def test_all_names_are_unique(self) -> None:
        self.assertEqual(len(audit.__all__), len(set(audit.__all__)))

    def test_all_names_are_strings(self) -> None:
        for name in audit.__all__:
            with self.subTest(name=name):
                self.assertIsInstance(name, str)


if __name__ == "__main__":
    unittest.main()
