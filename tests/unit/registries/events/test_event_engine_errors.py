"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_engine_errors.py
Layer: Event Unit Tests
Milestone: NPP-M006.2-T4 — Event Engine Error Tests
============================================================

Verifies the Event Engine exception hierarchy and inherited
EventError behavior.
"""

from __future__ import annotations

import unittest

from shared.events.event_engine_errors import (
    DuplicateHandlerRegistrationError,
    EventEngineError,
    HandlerExecutionError,
    HandlerNotRegisteredError,
    InvalidHandlerError,
)
from shared.events.event_errors import EventProcessingError


class EventEngineErrorTests(unittest.TestCase):
    """Unit tests for Event Engine exceptions."""

    def test_event_engine_error_inherits_event_processing_error(self) -> None:
        error = EventEngineError("Engine failure.")

        self.assertIsInstance(error, EventProcessingError)

    def test_specialized_errors_inherit_event_engine_error(self) -> None:
        error_types = (
            DuplicateHandlerRegistrationError,
            HandlerExecutionError,
            HandlerNotRegisteredError,
            InvalidHandlerError,
        )

        for error_type in error_types:
            with self.subTest(error_type=error_type.__name__):
                error = error_type("Engine failure.")

                self.assertIsInstance(error, EventEngineError)
                self.assertIsInstance(error, EventProcessingError)

    def test_inherited_message_normalization(self) -> None:
        error = HandlerExecutionError(
            "  Handler execution failed.  "
        )

        self.assertEqual(
            error.message,
            "Handler execution failed.",
        )

    def test_inherited_event_fields_are_preserved(self) -> None:
        error = HandlerNotRegisteredError(
            "No handler registered.",
            event_id=" EVT-000001 ",
            event_type=" TEST_EVENT ",
            metadata={"source": "unit"},
        )

        self.assertEqual(error.event_id, "EVT-000001")
        self.assertEqual(error.event_type, "TEST_EVENT")
        self.assertEqual(error.metadata["source"], "unit")

    def test_to_dict_uses_specialized_error_type(self) -> None:
        error = DuplicateHandlerRegistrationError(
            "Handler already registered.",
            event_type="TEST_EVENT",
        )

        data = error.to_dict()

        self.assertEqual(
            data["error_type"],
            "DuplicateHandlerRegistrationError",
        )
        self.assertEqual(
            data["message"],
            "Handler already registered.",
        )
        self.assertEqual(data["event_type"], "TEST_EVENT")


if __name__ == "__main__":
    unittest.main()
