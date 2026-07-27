"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_base_event.py
Layer: Event Unit Tests
Milestone: NPP-M006.1-T2 — Base Event Tests
============================================================

Verifies BaseEvent validation, normalization, immutability,
serialization, and interface compliance.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from types import MappingProxyType

from shared.events.base_event import BaseEvent
from shared.events.event_errors import EventValidationError
from shared.events.event_interface import EventInterface


class ConcreteEvent(BaseEvent):
    """Minimal concrete event used only for unit testing."""


class BaseEventTests(unittest.TestCase):

    def make_event(self, **overrides):
        data = {
            "event_id": " EVT-000001 ",
            "event_type": " TEST_EVENT ",
            "event_version": 1,
            "occurred_at": datetime.now(UTC),
            "metadata": {"source": "unit"},
            "payload": {"value": 1},
        }
        data.update(overrides)
        return ConcreteEvent(**data)

    def test_implements_event_interface(self):
        event = self.make_event()
        self.assertIsInstance(event, EventInterface)

    def test_constructor_normalizes_values(self):
        event = self.make_event()

        self.assertEqual(event.event_id, "EVT-000001")
        self.assertEqual(event.event_type, "TEST_EVENT")
        self.assertEqual(event.event_version, 1)
        self.assertEqual(event.occurred_at.tzinfo, UTC)

    def test_metadata_and_payload_are_read_only(self):
        metadata = {"source": "unit"}
        payload = {"value": 1}

        event = self.make_event(
            metadata=metadata,
            payload=payload,
        )

        metadata["source"] = "changed"
        payload["value"] = 99

        self.assertIsInstance(event.metadata, MappingProxyType)
        self.assertIsInstance(event.payload, MappingProxyType)

        self.assertEqual(event.metadata["source"], "unit")
        self.assertEqual(event.payload["value"], 1)

        with self.assertRaises(TypeError):
            event.metadata["source"] = "x"  # type: ignore[index]

        with self.assertRaises(TypeError):
            event.payload["value"] = 2  # type: ignore[index]

    def test_validate_passes_for_valid_event(self):
        self.assertIsNone(self.make_event().validate())

    def test_to_dict_returns_serializable_dictionary(self):
        event = self.make_event()
        data = event.to_dict()

        self.assertEqual(data["event_id"], "EVT-000001")
        self.assertEqual(data["event_type"], "TEST_EVENT")
        self.assertIsInstance(data["metadata"], dict)
        self.assertIsInstance(data["payload"], dict)

    def test_serialize_returns_valid_json(self):
        event = self.make_event()

        parsed = json.loads(event.serialize())

        self.assertEqual(parsed["event_id"], "EVT-000001")
        self.assertEqual(parsed["event_type"], "TEST_EVENT")

    def test_event_id_is_required(self):
        with self.assertRaisesRegex(
            ValueError,
            "event_id must not be empty",
        ):
            self.make_event(event_id=" ")

    def test_event_type_is_required(self):
        with self.assertRaisesRegex(
            ValueError,
            "event_type must not be empty",
        ):
            self.make_event(event_type=" ")

    def test_event_version_must_be_positive(self):
        with self.assertRaisesRegex(
            ValueError,
            "event_version must be greater than zero",
        ):
            self.make_event(event_version=0)

    def test_occurred_at_must_be_timezone_aware(self):
        with self.assertRaisesRegex(
            ValueError,
            "occurred_at must be timezone-aware",
        ):
            self.make_event(
                occurred_at=datetime.now()
            )

    def test_validate_raises_event_validation_error_for_invalid_state(self):
        event = self.make_event()
        event._event_version = 0  # test-only corruption

        with self.assertRaises(EventValidationError):
            event.validate()


if __name__ == "__main__":
    unittest.main()
