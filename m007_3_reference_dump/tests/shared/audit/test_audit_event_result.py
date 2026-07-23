"""Tests for shared.audit.audit_event_result."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from shared.audit.audit_event_result import AuditEventResult
from shared.audit.audit_event_types import AuditEventType
from shared.events.event_result import EventResult
from shared.events.event_status import EventStatus


def test_result_normalizes_audit_id_and_freezes_metadata() -> None:
    result = AuditEventResult.recorded(
        audit_id="  audit-001  ",
        event_id="event-001",
        metadata={"source": "audit-service"},
    )

    assert result.audit_id == "audit-001"
    assert isinstance(result.metadata, MappingProxyType)

    with pytest.raises(TypeError):
        result.metadata["new"] = "value"  # type: ignore[index]


def test_result_requires_non_empty_audit_id() -> None:
    with pytest.raises(ValueError, match="audit_id must not be empty"):
        AuditEventResult.recorded(audit_id="   ", event_id="event-001")


def test_result_requires_event_result() -> None:
    with pytest.raises(TypeError, match="EventResult"):
        AuditEventResult(audit_id="audit-001", event_result={})  # type: ignore[arg-type]


def test_result_rejects_non_audit_event_type() -> None:
    event_result = EventResult.created(
        event_id="event-001",
        event_type="provider.created",
    )

    with pytest.raises(ValueError, match="AuditEventType"):
        AuditEventResult(
            audit_id="audit-001",
            event_result=event_result,
        )


@pytest.mark.parametrize(
    ("factory_name", "event_type", "event_status"),
    [
        ("recorded", AuditEventType.RECORDED, EventStatus.CREATED),
        ("validated", AuditEventType.VALIDATED, EventStatus.VALIDATED),
        ("exported", AuditEventType.EXPORTED, EventStatus.PROCESSED),
        ("archived", AuditEventType.ARCHIVED, EventStatus.PROCESSED),
        ("purged", AuditEventType.PURGED, EventStatus.PROCESSED),
    ],
)
def test_success_factories(
    factory_name: str,
    event_type: AuditEventType,
    event_status: EventStatus,
) -> None:
    factory = getattr(AuditEventResult, factory_name)
    result = factory(audit_id="audit-001", event_id="event-001")

    assert result.success is True
    assert result.failed is False
    assert result.event_id == "event-001"
    assert result.event_type == event_type.value
    assert result.event_status is event_status


def test_failed_result_factory() -> None:
    result = AuditEventResult.failed_result(
        audit_id="audit-001",
        event_id="event-001",
        event_type=AuditEventType.EXPORTED,
        metadata={"reason": "backend unavailable"},
    )

    assert result.success is False
    assert result.failed is True
    assert result.event_status is EventStatus.FAILED
    assert result.event_type == "audit.exported"
    assert result.metadata == {"reason": "backend unavailable"}


def test_rejected_factory() -> None:
    result = AuditEventResult.rejected(
        audit_id="audit-001",
        event_id="event-001",
        event_type=AuditEventType.PURGED,
    )

    assert result.success is False
    assert result.event_status is EventStatus.REJECTED
    assert result.event_type == "audit.purged"


def test_failure_factories_require_typed_event_type() -> None:
    with pytest.raises(TypeError, match="AuditEventType"):
        AuditEventResult.failed_result(
            audit_id="audit-001",
            event_id="event-001",
            event_type="audit.exported",  # type: ignore[arg-type]
        )


def test_to_dict_returns_detached_data() -> None:
    result = AuditEventResult.recorded(
        audit_id="audit-001",
        event_id="event-001",
        metadata={"source": "audit-service"},
    )

    data = result.to_dict()

    assert data == {
        "audit_id": "audit-001",
        "event_result": {
            "success": True,
            "event_id": "event-001",
            "event_type": "audit.recorded",
            "event_status": "created",
            "message": "Audit record event created.",
            "metadata": {},
        },
        "metadata": {"source": "audit-service"},
    }

    data["metadata"]["source"] = "changed"
    assert result.metadata["source"] == "audit-service"
