"""M007.10 stabilization tests for the canonical AuditRecord contract."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from shared.audit.audit_action import AuditAction
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord


def _record(
    audit_id: str = "AUD-STABLE-001",
    *,
    metadata: dict[str, object] | None = None,
) -> AuditRecord:
    return AuditRecord(
        audit_id=audit_id,
        version=1,
        recorded_at=datetime(
            2026,
            7,
            24,
            12,
            30,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        action=AuditAction.PROCESS,
        outcome=AuditOutcome.SUCCESS,
        actor_id=" ACTOR-001 ",
        actor_type=" employee ",
        target_namespace=" nexfarm ",
        target_type=" grain_intake ",
        target_id=" INTAKE-001 ",
        runtime_id=" RUNTIME-001 ",
        runtime_mode=" simulation ",
        source=" nexapos-alpha ",
        event_id=" EVENT-001 ",
        event_type=" GRAIN_INTAKE_STARTED ",
        correlation_id=" CORR-001 ",
        causation_id=" CAUSE-001 ",
        request_id=" REQ-001 ",
        device_id=" DEVICE-001 ",
        metadata={"nested": {"value": 1}} if metadata is None else metadata,
    )


def test_record_normalization_and_derived_metadata_remain_consistent() -> None:
    record = _record()

    assert record.actor_id == "ACTOR-001"
    assert record.actor_type == "employee"
    assert record.runtime_mode == "simulation"
    assert record.source == "nexapos-alpha"
    assert record.recorded_at.tzinfo is timezone.utc

    assert record.actor.actor_id == record.actor_id
    assert record.actor.actor_type == record.actor_type
    assert record.source_metadata.source == record.source
    assert record.source_metadata.event_id == record.event_id
    assert record.source_metadata.event_type == record.event_type
    assert record.audit_metadata.actor == record.actor
    assert record.audit_metadata.source == record.source_metadata


def test_record_serialization_is_stable_and_detached() -> None:
    record = _record()
    serialized = record.to_dict()

    assert serialized["audit_id"] == "AUD-STABLE-001"
    assert serialized["action"] == "process"
    assert serialized["outcome"] == "success"
    assert serialized["recorded_at"].endswith("+00:00")

    serialized["metadata"]["nested"] = {"value": 99}
    assert record.metadata["nested"] == {"value": 1}


def test_record_defensively_copies_top_level_metadata() -> None:
    metadata = {"status": "original"}
    record = _record(metadata=metadata)

    metadata["status"] = "changed"

    assert record.metadata["status"] == "original"

    with pytest.raises(TypeError):
        record.metadata["status"] = "mutated"


def test_event_identifier_and_type_remain_an_atomic_pair() -> None:
    values = _record().to_dict()

    values["recorded_at"] = datetime.fromisoformat(values["recorded_at"])
    values["action"] = AuditAction(values["action"])
    values["outcome"] = AuditOutcome(values["outcome"])

    values["event_type"] = None

    with pytest.raises(Exception, match="event_id and event_type"):
        AuditRecord(**values)
