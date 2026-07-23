"""Tests for shared.audit.audit_event."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import MappingProxyType

import pytest

from shared.audit.audit_action import AuditAction
from shared.audit.audit_errors import AuditValidationError
from shared.audit.audit_event import AuditEvent
from shared.audit.audit_event_types import AuditEventType
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord
from shared.events.base_event import BaseEvent


def make_record(
    *,
    event_id: str | None = None,
    event_type: str | None = None,
) -> AuditRecord:
    return AuditRecord(
        audit_id="audit-001",
        version=1,
        recorded_at=datetime(2026, 7, 23, 10, 0, tzinfo=timezone.utc),
        action=AuditAction.CREATE,
        outcome=AuditOutcome.SUCCESS,
        actor_id="actor-001",
        actor_type="provider",
        target_namespace="identity",
        target_type="citizen",
        target_id="citizen-001",
        runtime_id="runtime-001",
        runtime_mode="simulation",
        source="provider-registry",
        event_id=event_id,
        event_type=event_type,
        metadata={"ip": "127.0.0.1"},
    )


def make_event(**overrides: object) -> AuditEvent:
    values: dict[str, object] = {
        "event_id": "event-001",
        "event_type": AuditEventType.RECORDED,
        "occurred_at": datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
        "record": make_record(),
        "event_version": 1,
        "metadata": {"source": "audit-service"},
    }
    values.update(overrides)
    return AuditEvent(**values)  # type: ignore[arg-type]


def test_audit_event_extends_base_event() -> None:
    assert isinstance(make_event(), BaseEvent)


def test_audit_event_normalizes_and_exposes_values() -> None:
    event = make_event(event_id="  event-001  ")

    assert event.event_id == "event-001"
    assert event.event_type == "audit.recorded"
    assert event.audit_event_type is AuditEventType.RECORDED
    assert event.event_version == 1
    assert event.occurred_at.tzinfo is timezone.utc
    assert event.record.audit_id == "audit-001"


def test_audit_event_metadata_and_payload_are_immutable() -> None:
    event = make_event()

    assert isinstance(event.metadata, MappingProxyType)
    assert isinstance(event.payload, MappingProxyType)

    with pytest.raises(TypeError):
        event.metadata["new"] = "value"  # type: ignore[index]

    with pytest.raises(TypeError):
        event.payload["new"] = "value"  # type: ignore[index]


def test_audit_event_requires_typed_event_type() -> None:
    with pytest.raises(TypeError, match="AuditEventType"):
        make_event(event_type="audit.recorded")


def test_audit_event_requires_audit_record() -> None:
    with pytest.raises(TypeError, match="AuditRecord"):
        make_event(record={})


def test_audit_event_converts_occurred_at_to_utc() -> None:
    offset = timezone(timedelta(hours=3))
    event = make_event(
        occurred_at=datetime(2026, 7, 23, 15, 0, tzinfo=offset)
    )

    assert event.occurred_at == datetime(
        2026, 7, 23, 12, 0, tzinfo=timezone.utc
    )


def test_validate_accepts_unlinked_record() -> None:
    make_event(record=make_record()).validate()


def test_validate_preserves_independent_source_event_trace() -> None:
    event = make_event(
        record=make_record(
            event_id="source-event-001",
            event_type="provider.registered",
        )
    )

    event.validate()

    assert event.event_id == "event-001"
    assert event.event_type == "audit.recorded"
    assert event.record.event_id == "source-event-001"
    assert event.record.event_type == "provider.registered"


def test_to_dict_returns_detached_serializable_data() -> None:
    event = make_event()

    data = event.to_dict()

    assert data["event_id"] == "event-001"
    assert data["event_type"] == "audit.recorded"
    assert data["event_version"] == 1
    assert data["occurred_at"] == "2026-07-23T12:00:00+00:00"
    assert data["metadata"] == {"source": "audit-service"}
    assert data["payload"]["record"]["audit_id"] == "audit-001"

    data["metadata"]["source"] = "changed"
    data["payload"]["record"]["metadata"]["ip"] = "changed"

    assert event.metadata["source"] == "audit-service"
    assert event.record.metadata["ip"] == "127.0.0.1"


def test_serialize_is_deterministic_json() -> None:
    event = make_event()

    serialized = event.serialize()

    assert '"event_id":"event-001"' in serialized
    assert '"event_type":"audit.recorded"' in serialized
    assert '"audit_id":"audit-001"' in serialized
