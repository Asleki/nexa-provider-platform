import json
from datetime import UTC, datetime
from types import MappingProxyType

import pytest

from registries.events import RegistryEvent, RegistryEventType
from shared.events import BaseEvent, EventMetadata
from shared.events.event_errors import EventValidationError


def make_metadata():
    return EventMetadata(correlation_id="corr-1", actor_id="actor-1")


def make_payload(**overrides):
    payload = {
        "registry_id": "npp.registry.birth",
        "registry_code": "BIRTH",
        "registry_family": "identity",
    }
    payload.update(overrides)
    return payload


def make_event(**overrides):
    values = {
        "event_id": "evt-1",
        "event_type": RegistryEventType.REGISTRY_REGISTERED,
        "occurred_at": datetime(2026, 7, 27, tzinfo=UTC),
        "event_metadata": make_metadata(),
        "payload": make_payload(),
    }
    values.update(overrides)
    return RegistryEvent(**values)


def test_registry_event_extends_shared_base_event():
    event = make_event()
    assert isinstance(event, BaseEvent)
    assert event.event_type == "registry.registered"
    assert event.registry_event_type is RegistryEventType.REGISTRY_REGISTERED
    assert event.registry_id == "npp.registry.birth"


def test_registry_event_preserves_typed_metadata_and_serializes():
    event = make_event()
    assert event.event_metadata.correlation_id == "corr-1"
    assert isinstance(event.payload, MappingProxyType)
    parsed = json.loads(event.serialize())
    assert parsed["metadata"]["correlation_id"] == "corr-1"
    assert parsed["payload"]["registry_code"] == "BIRTH"


def test_registry_event_normalizes_required_payload_text():
    event = make_event(payload=make_payload(registry_id=" npp.registry.birth "))
    assert event.registry_id == "npp.registry.birth"


@pytest.mark.parametrize("field", ["registry_id", "registry_code", "registry_family"])
def test_registry_event_rejects_missing_required_payload_fields(field):
    payload = make_payload()
    payload[field] = " "
    with pytest.raises(EventValidationError, match=field):
        make_event(payload=payload)


def test_status_changed_event_requires_transition_fields():
    with pytest.raises(EventValidationError, match="previous_status"):
        make_event(
            event_type=RegistryEventType.REGISTRY_STATUS_CHANGED,
            payload=make_payload(),
        )


def test_status_changed_event_rejects_equal_statuses():
    with pytest.raises(EventValidationError, match="different statuses"):
        make_event(
            event_type=RegistryEventType.REGISTRY_STATUS_CHANGED,
            payload=make_payload(previous_status="active", current_status="active"),
        )


def test_registry_event_requires_typed_event_type_and_metadata():
    with pytest.raises(TypeError, match="RegistryEventType"):
        make_event(event_type="registry.registered")
    with pytest.raises(TypeError, match="EventMetadata"):
        make_event(event_metadata={})
