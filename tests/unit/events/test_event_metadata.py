"""
============================================================
Nexa Provider Platform
File: tests/unit/events/test_event_metadata.py
Layer: Event Unit Tests
Milestone: NPP-M006.1-T7 — Event Metadata Tests
============================================================

Verifies EventMetadata validation, normalization,
immutability, UTC normalization, and serialization.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from types import MappingProxyType

from shared.events.event_metadata import EventMetadata


class EventMetadataTests(unittest.TestCase):

    def test_constructor_normalizes_fields(self) -> None:
        metadata = EventMetadata(
            correlation_id=" CORR-001 ",
            causation_id=" CAUSE-001 ",
            actor_id=" ACTOR-001 ",
            device_id=" DEV-001 ",
            source=" npp ",
            version=" 1.0 ",
        )

        self.assertEqual(metadata.correlation_id, "CORR-001")
        self.assertEqual(metadata.causation_id, "CAUSE-001")
        self.assertEqual(metadata.actor_id, "ACTOR-001")
        self.assertEqual(metadata.device_id, "DEV-001")
        self.assertEqual(metadata.source, "npp")
        self.assertEqual(metadata.version, "1.0")

    def test_required_fields_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "correlation_id must not be empty|correlation_id is required"):
            EventMetadata(correlation_id=" ")

    def test_created_at_is_normalized_to_utc(self) -> None:
        local = datetime(2026,1,1,12,0,tzinfo=timezone(timedelta(hours=2)))
        md = EventMetadata(correlation_id="CORR-001", created_at=local)
        self.assertEqual(md.created_at.tzinfo, UTC)
        self.assertEqual(md.created_at.hour,10)

    def test_naive_datetime_assumed_utc(self) -> None:
        naive = datetime(2026,1,1,12,0)
        md = EventMetadata(correlation_id="CORR-001", created_at=naive)
        self.assertEqual(md.created_at.tzinfo, UTC)
        self.assertEqual(md.created_at.hour,12)

    def test_created_at_must_be_datetime(self) -> None:
        with self.assertRaisesRegex(TypeError,"created_at must be a datetime"):
            EventMetadata(correlation_id="CORR-001", created_at="x")  # type: ignore

    def test_attributes_are_defensively_copied(self) -> None:
        attrs={"source":"unit"}
        md=EventMetadata(correlation_id="CORR-001",attributes=attrs)
        attrs["source"]="changed"
        self.assertIsInstance(md.attributes,MappingProxyType)
        self.assertEqual(md.attributes["source"],"unit")
        with self.assertRaises(TypeError):
            md.attributes["source"]="x"  # type: ignore[index]

    def test_attributes_must_be_mapping(self) -> None:
        with self.assertRaisesRegex(TypeError,"attributes must be a mapping"):
            EventMetadata(correlation_id="CORR-001",attributes=[])  # type: ignore

    def test_instance_is_frozen(self) -> None:
        md=EventMetadata(correlation_id="CORR-001")
        with self.assertRaises(FrozenInstanceError):
            md.source="x"  # type: ignore[misc]

    def test_to_dict_returns_plain_dictionary(self) -> None:
        md=EventMetadata(
            correlation_id="CORR-001",
            actor_id="ACT-1",
            attributes={"k":"v"},
        )
        data=md.to_dict()
        self.assertEqual(data["correlation_id"],"CORR-001")
        self.assertEqual(data["actor_id"],"ACT-1")
        self.assertIsInstance(data["attributes"],dict)
        self.assertIsInstance(data["created_at"],str)

    def test_to_dict_returns_independent_attribute_copy(self) -> None:
        md=EventMetadata(
            correlation_id="CORR-001",
            attributes={"k":"v"},
        )
        data=md.to_dict()
        data["attributes"]["k"]="changed"
        self.assertEqual(md.attributes["k"],"v")


if __name__=="__main__":
    unittest.main()
