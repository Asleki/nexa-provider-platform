"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_interface.py
Layer: Event Unit Tests
Milestone: NPP-M006.1-T1 — Event Interface Tests
============================================================

Verifies the implementation-independent EventInterface contract
used throughout the Nexa Provider Platform.

The tests ensure:

- EventInterface remains abstract.
- All required abstract members exist.
- Method signatures remain stable.
- A complete implementation becomes concrete.
- An incomplete implementation remains abstract.
"""

from __future__ import annotations

import inspect
import unittest
from datetime import datetime, UTC
from typing import Any, Mapping

from shared.events.event_interface import EventInterface


class ConcreteEvent(EventInterface):
    """Minimal concrete implementation used only for unit testing."""

    @property
    def event_id(self) -> str:
        return "EVT-000001"

    @property
    def event_type(self) -> str:
        return "TEST_EVENT"

    @property
    def event_version(self) -> int:
        return 1

    @property
    def occurred_at(self) -> datetime:
        return datetime.now(UTC)

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {}

    @property
    def payload(self) -> Mapping[str, Any]:
        return {}

    def validate(self) -> None:
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
        }

    def serialize(self) -> str:
        return "{}"


class IncompleteEvent(EventInterface):
    """Intentionally incomplete implementation."""

    pass


class EventInterfaceTests(unittest.TestCase):
    """Tests for the EventInterface contract."""

    def test_event_interface_is_abstract(self) -> None:
        self.assertTrue(inspect.isabstract(EventInterface))

        with self.assertRaises(TypeError):
            EventInterface()  # type: ignore[abstract]

    def test_incomplete_subclass_cannot_be_instantiated(self) -> None:
        self.assertTrue(inspect.isabstract(IncompleteEvent))

        with self.assertRaises(TypeError):
            IncompleteEvent()  # type: ignore[abstract]

    def test_complete_subclass_is_concrete(self) -> None:
        self.assertFalse(inspect.isabstract(ConcreteEvent))

        event = ConcreteEvent()

        self.assertIsInstance(event, EventInterface)

    def test_interface_declares_expected_abstract_members(self) -> None:
        expected_members = {
            "event_id",
            "event_type",
            "event_version",
            "occurred_at",
            "metadata",
            "payload",
            "validate",
            "to_dict",
            "serialize",
        }

        self.assertEqual(
            set(EventInterface.__abstractmethods__),
            expected_members,
        )

    def test_interface_method_signatures_are_stable(self) -> None:
        expected_parameter_names = {
            "validate": ("self",),
            "to_dict": ("self",),
            "serialize": ("self",),
        }

        for method_name, parameter_names in expected_parameter_names.items():
            with self.subTest(method=method_name):
                method = getattr(EventInterface, method_name)

                actual_names = tuple(
                    inspect.signature(method).parameters
                )

                self.assertEqual(
                    actual_names,
                    parameter_names,
                )

    def test_complete_implementation_returns_expected_types(
        self,
    ) -> None:
        event = ConcreteEvent()

        self.assertIsInstance(event.event_id, str)
        self.assertIsInstance(event.event_type, str)
        self.assertIsInstance(event.event_version, int)
        self.assertIsInstance(event.occurred_at, datetime)
        self.assertIsInstance(event.metadata, Mapping)
        self.assertIsInstance(event.payload, Mapping)

        self.assertIsNone(event.validate())

        self.assertIsInstance(
            event.to_dict(),
            dict,
        )

        self.assertIsInstance(
            event.serialize(),
            str,
        )


if __name__ == "__main__":
    unittest.main()