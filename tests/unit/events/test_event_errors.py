"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_errors.py
Layer: Event Unit Tests
Milestone: NPP-M006.1-T4 — Event Errors Tests
============================================================

Verifies the EventError hierarchy, validation, normalization,
immutability, and serialization.
"""

from __future__ import annotations

import unittest
from types import MappingProxyType

from shared.events.event_errors import (
    EventConflictError,
    EventError,
    EventNotFoundError,
    EventPersistenceError,
    EventProcessingError,
    EventSerializationError,
    EventValidationError,
)


class EventErrorTests(unittest.TestCase):

    def test_message_is_normalized(self) -> None:
        error = EventError("  Failure occurred.  ")
        self.assertEqual(error.message, "Failure occurred.")

    def test_message_must_be_string(self) -> None:
        for value in (None, 123, True, [], {}, object()):
            with self.subTest(message=value):
                with self.assertRaisesRegex(TypeError, "message must be a string"):
                    EventError(value)  # type: ignore[arg-type]

    def test_message_must_not_be_empty(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(message=value):
                with self.assertRaisesRegex(ValueError, "message must not be empty"):
                    EventError(value)

    def test_event_id_validation(self) -> None:
        with self.assertRaisesRegex(TypeError, "event_id must be a string"):
            EventError("Failure", event_id=123)  # type: ignore[arg-type]

        with self.assertRaisesRegex(
            ValueError,
            "event_id must not be empty when provided",
        ):
            EventError("Failure", event_id=" ")

    def test_event_type_validation(self) -> None:
        with self.assertRaisesRegex(TypeError, "event_type must be a string"):
            EventError("Failure", event_type=123)  # type: ignore[arg-type]

        with self.assertRaisesRegex(
            ValueError,
            "event_type must not be empty when provided",
        ):
            EventError("Failure", event_type=" ")

    def test_metadata_validation(self) -> None:
        for value in (None, 123, "x", [], object()):
            if value is None:
                continue
            with self.subTest(metadata=value):
                with self.assertRaisesRegex(TypeError, "metadata must be a mapping"):
                    EventError("Failure", metadata=value)  # type: ignore[arg-type]

    def test_metadata_is_defensively_copied(self) -> None:
        metadata = {"source": "unit"}

        error = EventError(
            "Failure",
            metadata=metadata,
        )

        metadata["source"] = "changed"

        self.assertIsInstance(error.metadata, MappingProxyType)
        self.assertEqual(error.metadata["source"], "unit")

        with self.assertRaises(TypeError):
            error.metadata["source"] = "changed"  # type: ignore[index]

    def test_to_dict_returns_plain_dictionary(self) -> None:
        error = EventValidationError(
            "Validation failed",
            event_id=" EVT-000001 ",
            event_type=" TEST_EVENT ",
            metadata={"field": "event_id"},
        )

        self.assertEqual(
            error.to_dict(),
            {
                "error_type": "EventValidationError",
                "message": "Validation failed",
                "event_id": "EVT-000001",
                "event_type": "TEST_EVENT",
                "metadata": {"field": "event_id"},
            },
        )

    def test_to_dict_returns_independent_metadata_copy(self) -> None:
        error = EventError(
            "Failure",
            metadata={"source": "unit"},
        )

        data = error.to_dict()
        data["metadata"]["source"] = "changed"

        self.assertEqual(error.metadata["source"], "unit")

    def test_error_hierarchy(self) -> None:
        subclasses = (
            EventValidationError,
            EventSerializationError,
            EventPersistenceError,
            EventProcessingError,
            EventNotFoundError,
            EventConflictError,
        )

        for cls in subclasses:
            with self.subTest(error_class=cls.__name__):
                instance = cls("Failure")
                self.assertIsInstance(instance, EventError)


if __name__ == "__main__":
    unittest.main()
