"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_status.py
Layer: Event Unit Tests
Milestone: NPP-M006.1-T6 — Event Status Tests
============================================================

Verifies EventStatus enum values, ordering, uniqueness,
string behavior, and helper properties.
"""

from __future__ import annotations

import unittest

from shared.events.event_status import EventStatus


class EventStatusTests(unittest.TestCase):
    """Unit tests for the EventStatus enumeration."""

    def test_event_status_values(self) -> None:
        self.assertEqual(EventStatus.CREATED.value, "created")
        self.assertEqual(EventStatus.VALIDATED.value, "validated")
        self.assertEqual(EventStatus.STORED.value, "stored")
        self.assertEqual(EventStatus.PROCESSED.value, "processed")
        self.assertEqual(EventStatus.FAILED.value, "failed")
        self.assertEqual(EventStatus.REJECTED.value, "rejected")

    def test_event_status_members_are_strings(self) -> None:
        for status in EventStatus:
            with self.subTest(status=status):
                self.assertIsInstance(status, str)
                self.assertIsInstance(status.value, str)

    def test_string_conversion_returns_enum_value(self) -> None:
        for status in EventStatus:
            with self.subTest(status=status):
                self.assertEqual(str(status), status.value)

    def test_event_status_member_order(self) -> None:
        self.assertEqual(
            tuple(EventStatus),
            (
                EventStatus.CREATED,
                EventStatus.VALIDATED,
                EventStatus.STORED,
                EventStatus.PROCESSED,
                EventStatus.FAILED,
                EventStatus.REJECTED,
            ),
        )

    def test_event_status_values_are_unique(self) -> None:
        values = [status.value for status in EventStatus]
        self.assertEqual(len(values), len(set(values)))

    def test_is_success_property(self) -> None:
        self.assertTrue(EventStatus.CREATED.is_success)
        self.assertTrue(EventStatus.VALIDATED.is_success)
        self.assertTrue(EventStatus.STORED.is_success)
        self.assertTrue(EventStatus.PROCESSED.is_success)
        self.assertFalse(EventStatus.FAILED.is_success)
        self.assertFalse(EventStatus.REJECTED.is_success)

    def test_is_terminal_property(self) -> None:
        self.assertFalse(EventStatus.CREATED.is_terminal)
        self.assertFalse(EventStatus.VALIDATED.is_terminal)
        self.assertFalse(EventStatus.STORED.is_terminal)
        self.assertTrue(EventStatus.PROCESSED.is_terminal)
        self.assertTrue(EventStatus.FAILED.is_terminal)
        self.assertTrue(EventStatus.REJECTED.is_terminal)


if __name__ == "__main__":
    unittest.main()
