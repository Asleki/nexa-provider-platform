"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_result.py
Layer: Event Unit Tests
Milestone: NPP-M006.1-T3 — Event Result Tests
============================================================

Verifies EventResult validation, normalization, immutability,
factory methods, lifecycle consistency, derived properties,
and serialization.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from types import MappingProxyType

from shared.events.event_result import EventResult
from shared.events.event_status import EventStatus


class EventResultTests(unittest.TestCase):
    """Unit tests for the standardized event-processing result."""

    def test_direct_construction_normalizes_text_fields(self) -> None:
        result = EventResult(
            success=True,
            event_id="  EVT-000001  ",
            event_type="  TEST_EVENT  ",
            event_status=EventStatus.CREATED,
            message="  Event created successfully.  ",
        )

        self.assertEqual(result.event_id, "EVT-000001")
        self.assertEqual(result.event_type, "TEST_EVENT")
        self.assertEqual(
            result.message,
            "Event created successfully.",
        )

    def test_success_must_be_boolean(self) -> None:
        invalid_values = (1, 0, "true", None, object())

        for value in invalid_values:
            with self.subTest(success=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "success must be a boolean",
                ):
                    EventResult(
                        success=value,  # type: ignore[arg-type]
                        event_id="EVT-000001",
                        event_type="TEST_EVENT",
                        event_status=EventStatus.CREATED,
                    )

    def test_event_id_must_be_string(self) -> None:
        invalid_values = (None, 123, True, [], {}, object())

        for value in invalid_values:
            with self.subTest(event_id=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "event_id must be a string",
                ):
                    EventResult(
                        success=True,
                        event_id=value,  # type: ignore[arg-type]
                        event_type="TEST_EVENT",
                        event_status=EventStatus.CREATED,
                    )

    def test_event_id_must_not_be_blank(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(event_id=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "event_id must not be empty",
                ):
                    EventResult(
                        success=True,
                        event_id=value,
                        event_type="TEST_EVENT",
                        event_status=EventStatus.CREATED,
                    )

    def test_event_type_must_be_string(self) -> None:
        invalid_values = (None, 123, True, [], {}, object())

        for value in invalid_values:
            with self.subTest(event_type=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "event_type must be a string",
                ):
                    EventResult(
                        success=True,
                        event_id="EVT-000001",
                        event_type=value,  # type: ignore[arg-type]
                        event_status=EventStatus.CREATED,
                    )

    def test_event_type_must_not_be_blank(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(event_type=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "event_type must not be empty",
                ):
                    EventResult(
                        success=True,
                        event_id="EVT-000001",
                        event_type=value,
                        event_status=EventStatus.CREATED,
                    )

    def test_event_status_must_be_event_status(self) -> None:
        invalid_values = ("created", 1, None, object())

        for value in invalid_values:
            with self.subTest(event_status=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "event_status must be an EventStatus value",
                ):
                    EventResult(
                        success=True,
                        event_id="EVT-000001",
                        event_type="TEST_EVENT",
                        event_status=value,  # type: ignore[arg-type]
                    )

    def test_message_must_be_string(self) -> None:
        invalid_values = (None, 123, True, [], {}, object())

        for value in invalid_values:
            with self.subTest(message=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "message must be a string",
                ):
                    EventResult(
                        success=True,
                        event_id="EVT-000001",
                        event_type="TEST_EVENT",
                        event_status=EventStatus.CREATED,
                        message=value,  # type: ignore[arg-type]
                    )

    def test_metadata_must_be_mapping(self) -> None:
        invalid_values = (None, 123, "metadata", [], object())

        for value in invalid_values:
            with self.subTest(metadata=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "metadata must be a mapping",
                ):
                    EventResult(
                        success=True,
                        event_id="EVT-000001",
                        event_type="TEST_EVENT",
                        event_status=EventStatus.CREATED,
                        metadata=value,  # type: ignore[arg-type]
                    )

    def test_successful_statuses_require_success_true(self) -> None:
        successful_statuses = (
            EventStatus.CREATED,
            EventStatus.VALIDATED,
            EventStatus.STORED,
            EventStatus.PROCESSED,
        )

        for status in successful_statuses:
            with self.subTest(event_status=status):
                with self.assertRaisesRegex(
                    ValueError,
                    "Successful event statuses require success=True",
                ):
                    EventResult(
                        success=False,
                        event_id="EVT-000001",
                        event_type="TEST_EVENT",
                        event_status=status,
                    )

    def test_failed_statuses_require_success_false(self) -> None:
        failed_statuses = (
            EventStatus.FAILED,
            EventStatus.REJECTED,
        )

        for status in failed_statuses:
            with self.subTest(event_status=status):
                with self.assertRaisesRegex(
                    ValueError,
                    "Failed event statuses require success=False",
                ):
                    EventResult(
                        success=True,
                        event_id="EVT-000001",
                        event_type="TEST_EVENT",
                        event_status=status,
                    )

    def test_result_instance_is_frozen(self) -> None:
        result = EventResult.created(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
        )

        with self.assertRaises(FrozenInstanceError):
            result.success = False  # type: ignore[misc]

    def test_metadata_is_defensively_copied_and_read_only(self) -> None:
        metadata = {"source": "unit"}

        result = EventResult.created(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
            metadata=metadata,
        )

        metadata["source"] = "changed"

        self.assertIsInstance(result.metadata, MappingProxyType)
        self.assertEqual(result.metadata["source"], "unit")

        with self.assertRaises(TypeError):
            result.metadata["source"] = "changed"  # type: ignore[index]

    def test_failed_property_reflects_success_flag(self) -> None:
        successful = EventResult.created(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
        )
        failed = EventResult.failed_result(
            event_id="EVT-000002",
            event_type="TEST_EVENT",
        )

        self.assertFalse(successful.failed)
        self.assertTrue(failed.failed)

    def test_created_factory_builds_expected_result(self) -> None:
        result = EventResult.created(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
            metadata={"source": "unit"},
        )

        self.assertTrue(result.success)
        self.assertFalse(result.failed)
        self.assertIs(result.event_status, EventStatus.CREATED)
        self.assertEqual(result.message, "Event created.")
        self.assertEqual(result.metadata["source"], "unit")

    def test_validated_factory_builds_expected_result(self) -> None:
        result = EventResult.validated(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
        )

        self.assertTrue(result.success)
        self.assertIs(result.event_status, EventStatus.VALIDATED)
        self.assertEqual(result.message, "Event validated.")

    def test_stored_factory_builds_expected_result(self) -> None:
        result = EventResult.stored(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
        )

        self.assertTrue(result.success)
        self.assertIs(result.event_status, EventStatus.STORED)
        self.assertEqual(result.message, "Event stored.")

    def test_processed_factory_builds_expected_result(self) -> None:
        result = EventResult.processed(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
        )

        self.assertTrue(result.success)
        self.assertIs(result.event_status, EventStatus.PROCESSED)
        self.assertEqual(result.message, "Event processed.")

    def test_failed_result_factory_builds_expected_result(self) -> None:
        result = EventResult.failed_result(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
        )

        self.assertFalse(result.success)
        self.assertTrue(result.failed)
        self.assertIs(result.event_status, EventStatus.FAILED)
        self.assertEqual(result.message, "Event processing failed.")

    def test_rejected_factory_builds_expected_result(self) -> None:
        result = EventResult.rejected(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
        )

        self.assertFalse(result.success)
        self.assertTrue(result.failed)
        self.assertIs(result.event_status, EventStatus.REJECTED)
        self.assertEqual(result.message, "Event rejected.")

    def test_factory_custom_message_is_preserved(self) -> None:
        result = EventResult.processed(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
            message="  Custom result message.  ",
        )

        self.assertEqual(result.message, "Custom result message.")

    def test_to_dict_returns_plain_serializable_structures(self) -> None:
        result = EventResult.stored(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
            metadata={"backend": "local"},
        )

        serialized = result.to_dict()

        self.assertEqual(
            serialized,
            {
                "success": True,
                "event_id": "EVT-000001",
                "event_type": "TEST_EVENT",
                "event_status": "stored",
                "message": "Event stored.",
                "metadata": {"backend": "local"},
            },
        )

        self.assertIsInstance(serialized["metadata"], dict)

    def test_to_dict_returns_independent_metadata_copy(self) -> None:
        result = EventResult.created(
            event_id="EVT-000001",
            event_type="TEST_EVENT",
            metadata={"source": "unit"},
        )

        serialized = result.to_dict()
        serialized["metadata"]["source"] = "changed"  # type: ignore[index]

        self.assertEqual(result.metadata["source"], "unit")


if __name__ == "__main__":
    unittest.main()
