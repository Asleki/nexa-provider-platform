"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_context.py
Layer: Event Unit Tests
Milestone: NPP-M006.2-T2 — Event Context Tests
============================================================

Verifies EventContext normalization, validation,
immutability, defensive copying, and serialization.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from types import MappingProxyType

from shared.events.event_context import EventContext


class EventContextTests(unittest.TestCase):
    """Unit tests for EventContext."""

    def test_constructor_defaults(self) -> None:
        context = EventContext()

        self.assertEqual(context.runtime_mode, "production")
        self.assertIsNone(context.actor_id)
        self.assertEqual(context.source, "npp")
        self.assertIsNone(context.correlation_id)
        self.assertEqual(dict(context.attributes), {})

    def test_constructor_normalizes_text_fields(self) -> None:
        context = EventContext(
            runtime_mode=" simulation ",
            actor_id=" ACTOR-001 ",
            source=" provider-api ",
            correlation_id=" CORR-001 ",
        )

        self.assertEqual(context.runtime_mode, "simulation")
        self.assertEqual(context.actor_id, "ACTOR-001")
        self.assertEqual(context.source, "provider-api")
        self.assertEqual(context.correlation_id, "CORR-001")

    def test_optional_blank_fields_become_none(self) -> None:
        context = EventContext(
            actor_id="   ",
            correlation_id="   ",
        )

        self.assertIsNone(context.actor_id)
        self.assertIsNone(context.correlation_id)

    def test_runtime_mode_must_be_string(self) -> None:
        invalid_values = (None, 123, True, [], {}, object())

        for value in invalid_values:
            with self.subTest(runtime_mode=value):
                expected_error = ValueError if value is None else TypeError

                with self.assertRaises(expected_error):
                    EventContext(runtime_mode=value)  # type: ignore[arg-type]

    def test_runtime_mode_must_not_be_empty(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(runtime_mode=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "runtime_mode must not be empty",
                ):
                    EventContext(runtime_mode=value)

    def test_source_must_be_string(self) -> None:
        invalid_values = (None, 123, True, [], {}, object())

        for value in invalid_values:
            with self.subTest(source=value):
                expected_error = ValueError if value is None else TypeError

                with self.assertRaises(expected_error):
                    EventContext(source=value)  # type: ignore[arg-type]

    def test_source_must_not_be_empty(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(source=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "source must not be empty",
                ):
                    EventContext(source=value)

    def test_optional_text_fields_must_be_strings(self) -> None:
        invalid_values = (123, True, [], {}, object())

        for field_name in ("actor_id", "correlation_id"):
            for value in invalid_values:
                with self.subTest(field=field_name, value=value):
                    with self.assertRaisesRegex(
                        TypeError,
                        f"{field_name} must be a string",
                    ):
                        EventContext(**{field_name: value})

    def test_attributes_must_be_mapping(self) -> None:
        invalid_values = (None, 123, "attributes", [], object())

        for value in invalid_values:
            with self.subTest(attributes=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "attributes must be a mapping",
                ):
                    EventContext(attributes=value)  # type: ignore[arg-type]

    def test_attributes_are_defensively_copied_and_read_only(self) -> None:
        attributes = {"request_id": "REQ-001"}

        context = EventContext(attributes=attributes)
        attributes["request_id"] = "CHANGED"

        self.assertIsInstance(context.attributes, MappingProxyType)
        self.assertEqual(context.attributes["request_id"], "REQ-001")

        with self.assertRaises(TypeError):
            context.attributes["request_id"] = "CHANGED"  # type: ignore[index]

    def test_instance_is_frozen(self) -> None:
        context = EventContext()

        with self.assertRaises(FrozenInstanceError):
            context.source = "changed"  # type: ignore[misc]

    def test_to_dict_returns_plain_dictionary(self) -> None:
        context = EventContext(
            runtime_mode="simulation",
            actor_id="ACTOR-001",
            source="unit-test",
            correlation_id="CORR-001",
            attributes={"request_id": "REQ-001"},
        )

        self.assertEqual(
            context.to_dict(),
            {
                "runtime_mode": "simulation",
                "actor_id": "ACTOR-001",
                "source": "unit-test",
                "correlation_id": "CORR-001",
                "attributes": {"request_id": "REQ-001"},
            },
        )

    def test_to_dict_returns_independent_attribute_copy(self) -> None:
        context = EventContext(
            attributes={"request_id": "REQ-001"},
        )

        serialized = context.to_dict()
        serialized["attributes"]["request_id"] = "CHANGED"

        self.assertEqual(
            context.attributes["request_id"],
            "REQ-001",
        )


if __name__ == "__main__":
    unittest.main()
