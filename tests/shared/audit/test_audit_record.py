"""
============================================================
Nexa Provider Platform
File: tests/shared/audit/test_audit_record.py
Layer: Shared Audit Tests
Milestone: NPP-M007.1-T4 — Audit Record Tests
============================================================

Verifies AuditRecord validation, normalization, immutability,
UTC handling, metadata protection, trace consistency, and
serialization.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from types import MappingProxyType

from shared.audit.audit_action import AuditAction
from shared.audit.audit_errors import (
    AuditIdentifierError,
    AuditMetadataError,
    AuditTimestampError,
    AuditValidationError,
)
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord


class AuditRecordTests(unittest.TestCase):

    @staticmethod
    def _make_record(**overrides: object) -> AuditRecord:
        values: dict[str, object] = {
            "audit_id": "AUD-000001",
            "version": 1,
            "recorded_at": datetime(
                2026,
                1,
                1,
                12,
                0,
                tzinfo=UTC,
            ),
            "action": AuditAction.CREATE,
            "outcome": AuditOutcome.SUCCESS,
            "actor_id": "ACTOR-001",
            "actor_type": "employee",
            "target_namespace": "registry",
            "target_type": "citizen",
            "target_id": "CITIZEN-001",
            "runtime_id": "RUN-001",
            "runtime_mode": "production",
            "source": "npp",
        }
        values.update(overrides)
        return AuditRecord(**values)  # type: ignore[arg-type]

    def test_constructor_normalizes_required_fields(self) -> None:
        record = self._make_record(
            audit_id=" AUD-000001 ",
            actor_id=" ACTOR-001 ",
            actor_type=" employee ",
            target_namespace=" registry ",
            target_type=" citizen ",
            target_id=" CITIZEN-001 ",
            runtime_id=" RUN-001 ",
            runtime_mode=" production ",
            source=" npp ",
        )

        self.assertEqual(record.audit_id, "AUD-000001")
        self.assertEqual(record.actor_id, "ACTOR-001")
        self.assertEqual(record.actor_type, "employee")
        self.assertEqual(record.target_namespace, "registry")
        self.assertEqual(record.target_type, "citizen")
        self.assertEqual(record.target_id, "CITIZEN-001")
        self.assertEqual(record.runtime_id, "RUN-001")
        self.assertEqual(record.runtime_mode, "production")
        self.assertEqual(record.source, "npp")

    def test_constructor_normalizes_optional_fields(self) -> None:
        record = self._make_record(
            event_id=" EVT-001 ",
            event_type=" CITIZEN_CREATED ",
            correlation_id=" CORR-001 ",
            causation_id=" CAUSE-001 ",
            request_id=" REQ-001 ",
            device_id=" DEV-001 ",
        )

        self.assertEqual(record.event_id, "EVT-001")
        self.assertEqual(record.event_type, "CITIZEN_CREATED")
        self.assertEqual(record.correlation_id, "CORR-001")
        self.assertEqual(record.causation_id, "CAUSE-001")
        self.assertEqual(record.request_id, "REQ-001")
        self.assertEqual(record.device_id, "DEV-001")

    def test_audit_id_validation(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(audit_id=value):
                with self.assertRaises(AuditIdentifierError):
                    self._make_record(audit_id=value)

        with self.assertRaises(AuditIdentifierError):
            self._make_record(audit_id=123)

    def test_version_validation(self) -> None:
        for value in (True, False, 0, -1, 1.5, "1"):
            with self.subTest(version=value):
                with self.assertRaises(AuditValidationError):
                    self._make_record(version=value)

    def test_recorded_at_is_normalized_to_utc(self) -> None:
        local_time = datetime(
            2026,
            1,
            1,
            12,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        )

        record = self._make_record(recorded_at=local_time)

        self.assertEqual(record.recorded_at.tzinfo, UTC)
        self.assertEqual(record.recorded_at.hour, 10)

    def test_recorded_at_must_be_timezone_aware_datetime(self) -> None:
        invalid_values = (
            datetime(2026, 1, 1, 12, 0),
            "2026-01-01T12:00:00Z",
            None,
        )

        for value in invalid_values:
            with self.subTest(recorded_at=value):
                with self.assertRaises(AuditTimestampError):
                    self._make_record(recorded_at=value)

    def test_action_must_be_audit_action(self) -> None:
        for value in ("create", 1, None):
            with self.subTest(action=value):
                with self.assertRaises(AuditValidationError):
                    self._make_record(action=value)

    def test_outcome_must_be_audit_outcome(self) -> None:
        for value in ("success", 1, None):
            with self.subTest(outcome=value):
                with self.assertRaises(AuditValidationError):
                    self._make_record(outcome=value)

    def test_required_text_fields_validation(self) -> None:
        field_names = (
            "actor_id",
            "actor_type",
            "target_namespace",
            "target_type",
            "target_id",
            "runtime_id",
            "runtime_mode",
            "source",
        )

        for field_name in field_names:
            with self.subTest(field=field_name, value=" "):
                with self.assertRaises(AuditValidationError):
                    self._make_record(**{field_name: " "})

            with self.subTest(field=field_name, value=123):
                with self.assertRaises(AuditValidationError):
                    self._make_record(**{field_name: 123})

    def test_optional_text_fields_validation(self) -> None:
        field_names = (
            "correlation_id",
            "causation_id",
            "request_id",
            "device_id",
        )

        for field_name in field_names:
            with self.subTest(field=field_name, value=" "):
                with self.assertRaises(AuditValidationError):
                    self._make_record(**{field_name: " "})

            with self.subTest(field=field_name, value=123):
                with self.assertRaises(AuditValidationError):
                    self._make_record(**{field_name: 123})

    def test_event_id_and_event_type_must_be_provided_together(self) -> None:
        with self.assertRaisesRegex(
            AuditValidationError,
            "event_id and event_type must be provided together",
        ):
            self._make_record(event_id="EVT-001")

        with self.assertRaisesRegex(
            AuditValidationError,
            "event_id and event_type must be provided together",
        ):
            self._make_record(event_type="CITIZEN_CREATED")

    def test_metadata_is_defensively_copied(self) -> None:
        metadata = {"channel": "api"}

        record = self._make_record(metadata=metadata)
        metadata["channel"] = "changed"

        self.assertIsInstance(record.metadata, MappingProxyType)
        self.assertEqual(record.metadata["channel"], "api")

        with self.assertRaises(TypeError):
            record.metadata["channel"] = "changed"  # type: ignore[index]

    def test_metadata_must_be_mapping(self) -> None:
        for value in (None, "x", 123, [], object()):
            with self.subTest(metadata=value):
                with self.assertRaises(AuditMetadataError):
                    self._make_record(metadata=value)

    def test_instance_is_frozen(self) -> None:
        record = self._make_record()

        with self.assertRaises(FrozenInstanceError):
            record.source = "changed"  # type: ignore[misc]

    def test_to_dict_returns_plain_dictionary(self) -> None:
        record = self._make_record(
            event_id="EVT-001",
            event_type="CITIZEN_CREATED",
            correlation_id="CORR-001",
            causation_id="CAUSE-001",
            request_id="REQ-001",
            device_id="DEV-001",
            metadata={"channel": "api"},
        )

        data = record.to_dict()

        self.assertEqual(
            data,
            {
                "audit_id": "AUD-000001",
                "version": 1,
                "recorded_at": "2026-01-01T12:00:00+00:00",
                "action": "create",
                "outcome": "success",
                "actor_id": "ACTOR-001",
                "actor_type": "employee",
                "target_namespace": "registry",
                "target_type": "citizen",
                "target_id": "CITIZEN-001",
                "runtime_id": "RUN-001",
                "runtime_mode": "production",
                "source": "npp",
                "event_id": "EVT-001",
                "event_type": "CITIZEN_CREATED",
                "correlation_id": "CORR-001",
                "causation_id": "CAUSE-001",
                "request_id": "REQ-001",
                "device_id": "DEV-001",
                "metadata": {"channel": "api"},
            },
        )
        self.assertIsInstance(data["metadata"], dict)

    def test_to_dict_returns_independent_metadata_copy(self) -> None:
        record = self._make_record(metadata={"channel": "api"})

        data = record.to_dict()
        data["metadata"]["channel"] = "changed"

        self.assertEqual(record.metadata["channel"], "api")


if __name__ == "__main__":
    unittest.main()
