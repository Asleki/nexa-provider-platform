"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_envelope.py
Layer: Event Unit Tests
Milestone: NPP-M006.2-T3 — Event Envelope Tests
============================================================

Verifies EventEnvelope validation, immutability,
property forwarding, and serialization.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

from shared.events.base_event import BaseEvent
from shared.events.event_context import EventContext
from shared.events.event_envelope import EventEnvelope


class ConcreteEvent(BaseEvent):
    """Minimal concrete event."""


class EventEnvelopeTests(unittest.TestCase):

    def make_event(self):
        return ConcreteEvent(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
            event_version=1,
            occurred_at=datetime.now(UTC),
            metadata={"source": "unit"},
            payload={"value": 1},
        )

    def test_constructor_accepts_valid_objects(self):
        envelope = EventEnvelope(self.make_event(), EventContext())
        self.assertIsInstance(envelope, EventEnvelope)

    def test_event_must_implement_event_interface(self):
        with self.assertRaisesRegex(TypeError, "event must implement EventInterface"):
            EventEnvelope(object(), EventContext())  # type: ignore[arg-type]

    def test_context_must_be_event_context(self):
        with self.assertRaisesRegex(TypeError, "context must be an EventContext"):
            EventEnvelope(self.make_event(), object())  # type: ignore[arg-type]

    def test_event_id_property(self):
        self.assertEqual(
            EventEnvelope(self.make_event(), EventContext()).event_id,
            "EVT-000001",
        )

    def test_event_type_property(self):
        self.assertEqual(
            EventEnvelope(self.make_event(), EventContext()).event_type,
            "TEST_EVENT",
        )

    def test_instance_is_frozen(self):
        envelope = EventEnvelope(self.make_event(), EventContext())
        with self.assertRaises(FrozenInstanceError):
            envelope.event = self.make_event()  # type: ignore[misc]

    def test_to_dict_returns_plain_dictionary(self):
        envelope = EventEnvelope(
            self.make_event(),
            EventContext(attributes={"request_id": "REQ-001"}),
        )
        data = envelope.to_dict()
        self.assertEqual(data["event"]["event_id"], "EVT-000001")
        self.assertEqual(data["event"]["event_type"], "TEST_EVENT")
        self.assertEqual(
            data["context"]["attributes"]["request_id"],
            "REQ-001",
        )


if __name__ == "__main__":
    unittest.main()
