"""
============================================================
Nexa Provider Platform
File: tests/shared/audit/test_audit_action.py
Layer: Shared Audit Tests
Milestone: NPP-M007.1-T3 — Audit Action Tests
============================================================

Verifies AuditAction values, string conversion, enum behavior,
lookup by serialized value, and invalid-value rejection.
"""

from __future__ import annotations

import unittest
from enum import Enum

from shared.audit.audit_action import AuditAction


class AuditActionTests(unittest.TestCase):

    def test_action_is_string_enum(self) -> None:
        self.assertTrue(issubclass(AuditAction, str))
        self.assertTrue(issubclass(AuditAction, Enum))

    def test_declared_values(self) -> None:
        self.assertEqual(
            [action.value for action in AuditAction],
            [
                "create",
                "read",
                "update",
                "delete",
                "list",
                "validate",
                "process",
                "login",
                "logout",
                "register",
            ],
        )

    def test_string_conversion_returns_value(self) -> None:
        expected_values = {
            AuditAction.CREATE: "create",
            AuditAction.READ: "read",
            AuditAction.UPDATE: "update",
            AuditAction.DELETE: "delete",
            AuditAction.LIST: "list",
            AuditAction.VALIDATE: "validate",
            AuditAction.PROCESS: "process",
            AuditAction.LOGIN: "login",
            AuditAction.LOGOUT: "logout",
            AuditAction.REGISTER: "register",
        }

        for action, expected_value in expected_values.items():
            with self.subTest(action=action.name):
                self.assertEqual(str(action), expected_value)

    def test_lookup_by_value(self) -> None:
        expected_members = {
            "create": AuditAction.CREATE,
            "read": AuditAction.READ,
            "update": AuditAction.UPDATE,
            "delete": AuditAction.DELETE,
            "list": AuditAction.LIST,
            "validate": AuditAction.VALIDATE,
            "process": AuditAction.PROCESS,
            "login": AuditAction.LOGIN,
            "logout": AuditAction.LOGOUT,
            "register": AuditAction.REGISTER,
        }

        for value, expected_member in expected_members.items():
            with self.subTest(value=value):
                self.assertIs(AuditAction(value), expected_member)

    def test_invalid_value_is_rejected(self) -> None:
        for value in (
            "",
            "CREATE",
            "unknown",
            " create ",
            "approve",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    AuditAction(value)

    def test_members_compare_as_strings(self) -> None:
        expected_values = {
            AuditAction.CREATE: "create",
            AuditAction.READ: "read",
            AuditAction.UPDATE: "update",
            AuditAction.DELETE: "delete",
            AuditAction.LIST: "list",
            AuditAction.VALIDATE: "validate",
            AuditAction.PROCESS: "process",
            AuditAction.LOGIN: "login",
            AuditAction.LOGOUT: "logout",
            AuditAction.REGISTER: "register",
        }

        for action, expected_value in expected_values.items():
            with self.subTest(action=action.name):
                self.assertEqual(action, expected_value)

    def test_member_names_are_stable(self) -> None:
        self.assertEqual(
            [action.name for action in AuditAction],
            [
                "CREATE",
                "READ",
                "UPDATE",
                "DELETE",
                "LIST",
                "VALIDATE",
                "PROCESS",
                "LOGIN",
                "LOGOUT",
                "REGISTER",
            ],
        )


if __name__ == "__main__":
    unittest.main()
