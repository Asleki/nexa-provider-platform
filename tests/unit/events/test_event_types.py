"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_types.py
Layer: Event Unit Tests
Milestone: NPP-M006.1-T5 — Event Types Tests
============================================================

Verifies EventType enum values, ordering, uniqueness,
string behavior, and serialization.
"""

from __future__ import annotations

import unittest

from shared.events.event_types import EventType


class EventTypesTests(unittest.TestCase):
    """Unit tests for the EventType enumeration."""

    def test_event_type_values(self) -> None:
        self.assertEqual(EventType.IDENTITY.value, "identity")
        self.assertEqual(EventType.PROVIDER.value, "provider")
        self.assertEqual(EventType.REGISTRY.value, "registry")
        self.assertEqual(EventType.VERIFICATION.value, "verification")
        self.assertEqual(EventType.AUDIT.value, "audit")
        self.assertEqual(EventType.SYSTEM.value, "system")
        self.assertEqual(
            EventType.SYNCHRONIZATION.value,
            "synchronization",
        )

    def test_event_type_members_are_strings(self) -> None:
        for event_type in EventType:
            with self.subTest(event_type=event_type):
                self.assertIsInstance(event_type, str)
                self.assertIsInstance(event_type.value, str)

    def test_string_conversion_returns_enum_value(self) -> None:
        for event_type in EventType:
            with self.subTest(event_type=event_type):
                self.assertEqual(
                    str(event_type),
                    event_type.value,
                )

    def test_event_type_member_order(self) -> None:
        self.assertEqual(
            tuple(EventType),
            (
                EventType.IDENTITY,
                EventType.PROVIDER,
                EventType.REGISTRY,
                EventType.VERIFICATION,
                EventType.AUDIT,
                EventType.SYSTEM,
                EventType.SYNCHRONIZATION,
            ),
        )

    def test_event_type_values_are_unique(self) -> None:
        values = [member.value for member in EventType]

        self.assertEqual(
            len(values),
            len(set(values)),
        )


if __name__ == "__main__":
    unittest.main()
