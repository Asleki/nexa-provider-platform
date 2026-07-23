"""
============================================================
Nexa Provider Platform
File: tests/shared/audit/test_audit_outcome.py
Layer: Shared Audit Tests
Milestone: NPP-M007.1-T2 — Audit Outcome Tests
============================================================

Verifies AuditOutcome values, string conversion, success and
failure classification helpers, enum behavior, and serialization.
"""

from __future__ import annotations

import unittest
from enum import Enum

from shared.audit.audit_outcome import AuditOutcome


class AuditOutcomeTests(unittest.TestCase):

    def test_outcome_is_string_enum(self) -> None:
        self.assertTrue(issubclass(AuditOutcome, str))
        self.assertTrue(issubclass(AuditOutcome, Enum))

    def test_declared_values(self) -> None:
        self.assertEqual(
            [outcome.value for outcome in AuditOutcome],
            [
                "success",
                "failure",
                "rejected",
            ],
        )

    def test_string_conversion_returns_value(self) -> None:
        expected_values = {
            AuditOutcome.SUCCESS: "success",
            AuditOutcome.FAILURE: "failure",
            AuditOutcome.REJECTED: "rejected",
        }

        for outcome, expected_value in expected_values.items():
            with self.subTest(outcome=outcome.name):
                self.assertEqual(str(outcome), expected_value)

    def test_is_success(self) -> None:
        expected_results = {
            AuditOutcome.SUCCESS: True,
            AuditOutcome.FAILURE: False,
            AuditOutcome.REJECTED: False,
        }

        for outcome, expected_result in expected_results.items():
            with self.subTest(outcome=outcome.name):
                self.assertIs(outcome.is_success, expected_result)

    def test_is_failure(self) -> None:
        expected_results = {
            AuditOutcome.SUCCESS: False,
            AuditOutcome.FAILURE: True,
            AuditOutcome.REJECTED: True,
        }

        for outcome, expected_result in expected_results.items():
            with self.subTest(outcome=outcome.name):
                self.assertIs(outcome.is_failure, expected_result)

    def test_success_and_failure_are_mutually_exclusive(self) -> None:
        for outcome in AuditOutcome:
            with self.subTest(outcome=outcome.name):
                self.assertNotEqual(
                    outcome.is_success,
                    outcome.is_failure,
                )

    def test_lookup_by_value(self) -> None:
        expected_members = {
            "success": AuditOutcome.SUCCESS,
            "failure": AuditOutcome.FAILURE,
            "rejected": AuditOutcome.REJECTED,
        }

        for value, expected_member in expected_members.items():
            with self.subTest(value=value):
                self.assertIs(AuditOutcome(value), expected_member)

    def test_invalid_value_is_rejected(self) -> None:
        for value in ("", "SUCCESS", "unknown", " success "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    AuditOutcome(value)

    def test_members_compare_as_strings(self) -> None:
        self.assertEqual(AuditOutcome.SUCCESS, "success")
        self.assertEqual(AuditOutcome.FAILURE, "failure")
        self.assertEqual(AuditOutcome.REJECTED, "rejected")


if __name__ == "__main__":
    unittest.main()
