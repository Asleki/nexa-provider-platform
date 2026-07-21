"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_engine.py
Layer: Event Unit Tests
Milestone: NPP-M006.2-T5 — Event Engine Tests (v003)
============================================================
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from shared.events.base_event import BaseEvent
from shared.events.event_context import EventContext
from shared.events.event_engine import EventEngine
from shared.events.event_engine_errors import (
    DuplicateHandlerRegistrationError,
    HandlerExecutionError,
    HandlerNotRegisteredError,
    InvalidHandlerError,
)
from shared.events.event_envelope import EventEnvelope
from shared.events.event_handler import EventHandler
from shared.events.event_result import EventResult


class DemoEvent(BaseEvent):
    pass


class DemoHandler(EventHandler[DemoEvent]):
    @property
    def event_type(self):
        return "DEMO"

    def can_handle(self, event):
        return event.event_type == "DEMO"

    def handle(self, event):
        return EventResult.processed(
            event_id=event.event_id,
            event_type=event.event_type,
        )


class RejectingHandler(DemoHandler):
    def can_handle(self, event):
        return False


class FailingHandler(DemoHandler):
    def handle(self, event):
        raise RuntimeError("boom")


class InvalidHandler:
    pass


class EventEngineTests(unittest.TestCase):

    def make_envelope(self):
        event = DemoEvent(
            event_id="EVT-1",
            event_type="DEMO",
            event_version=1,
            occurred_at=datetime.now(UTC),
            metadata={},
            payload={},
        )
        return EventEnvelope(event=event, context=EventContext())

    def test_register_and_process(self):
        engine = EventEngine()
        engine.register_handler(DemoHandler())
        result = engine.process(self.make_envelope())
        self.assertTrue(result.success)

    def test_duplicate_registration(self):
        engine = EventEngine()
        engine.register_handler(DemoHandler())
        with self.assertRaises(DuplicateHandlerRegistrationError):
            engine.register_handler(DemoHandler())

    def test_invalid_handler(self):
        with self.assertRaises(InvalidHandlerError):
            EventEngine().register_handler(InvalidHandler())  # type: ignore[arg-type]

    def test_missing_handler(self):
        with self.assertRaises(HandlerNotRegisteredError):
            EventEngine().process(self.make_envelope())

    def test_handler_rejected(self):
        engine = EventEngine()
        engine.register_handler(RejectingHandler())
        with self.assertRaises(HandlerNotRegisteredError):
            engine.process(self.make_envelope())

    def test_handler_execution_error(self):
        engine = EventEngine()
        engine.register_handler(FailingHandler())
        with self.assertRaises(HandlerExecutionError):
            engine.process(self.make_envelope())


if __name__ == "__main__":
    unittest.main()
