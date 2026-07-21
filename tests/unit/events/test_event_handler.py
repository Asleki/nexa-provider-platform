"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_handler.py
Layer: Event Unit Tests
Milestone: NPP-M006.2-T1 — Event Handler Tests
============================================================

Verifies the EventHandler contract.
"""

from __future__ import annotations

import inspect
import unittest

from shared.events.event_handler import EventHandler
from shared.events.event_interface import EventInterface
from shared.events.event_result import EventResult


class ConcreteEvent(EventInterface):
    @property
    def event_id(self) -> str: return "EVT-1"
    @property
    def event_type(self) -> str: return "TEST_EVENT"
    @property
    def event_version(self) -> int: return 1
    @property
    def occurred_at(self):
        from datetime import UTC, datetime
        return datetime.now(UTC)
    @property
    def metadata(self): return {}
    @property
    def payload(self): return {}
    def validate(self) -> None: return None
    def to_dict(self): return {}
    def serialize(self) -> str: return "{}"


class CompleteHandler(EventHandler[ConcreteEvent]):
    @property
    def event_type(self) -> str:
        return "TEST_EVENT"

    def can_handle(self, event: EventInterface) -> bool:
        return event.event_type == self.event_type

    def handle(self, event: ConcreteEvent) -> EventResult:
        return EventResult.processed(
            event_id=event.event_id,
            event_type=event.event_type,
        )


class IncompleteHandler(EventHandler):
    pass


class EventHandlerTests(unittest.TestCase):

    def test_event_handler_is_abstract(self):
        self.assertTrue(inspect.isabstract(EventHandler))
        with self.assertRaises(TypeError):
            EventHandler()  # type: ignore

    def test_incomplete_handler_is_abstract(self):
        self.assertTrue(inspect.isabstract(IncompleteHandler))
        with self.assertRaises(TypeError):
            IncompleteHandler()  # type: ignore

    def test_complete_handler_is_concrete(self):
        handler = CompleteHandler()
        self.assertIsInstance(handler, EventHandler)

    def test_can_handle(self):
        handler = CompleteHandler()
        self.assertTrue(handler.can_handle(ConcreteEvent()))

    def test_handle_returns_event_result(self):
        result = CompleteHandler().handle(ConcreteEvent())
        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
