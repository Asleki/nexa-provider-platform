from datetime import UTC, datetime

import pytest

from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily, RegistryStatus
from registries.events import RegistryEventFactory, RegistryEventType
from registries.governance import RegistryLifecycle
from shared.events import EventMetadata

NOW = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)


def make_registry(status=RegistryStatus.DRAFT):
    return BaseRegistry(
        RegistryDefinition(
            registry_id="npp.registry.birth",
            registry_code="BIRTH",
            registry_name="Birth Registry",
            family=RegistryFamily.SHARED_INFRASTRUCTURE,
            status=status,
        )
    )


def make_factory():
    return RegistryEventFactory(
        event_id_factory=lambda: "evt-fixed",
        clock=lambda: NOW,
    )


def metadata():
    return EventMetadata(correlation_id="corr-fixed", source="unit-tests")


@pytest.mark.parametrize(
    ("method", "expected_type"),
    [
        ("registered", RegistryEventType.REGISTRY_REGISTERED),
        ("replaced", RegistryEventType.REGISTRY_REPLACED),
        ("removed", RegistryEventType.REGISTRY_REMOVED),
    ],
)
def test_factory_creates_registry_snapshot_events(method, expected_type):
    event = getattr(make_factory(), method)(make_registry(), metadata=metadata())
    assert event.event_id == "evt-fixed"
    assert event.occurred_at == NOW
    assert event.registry_event_type is expected_type
    assert event.payload["registry_id"] == "npp.registry.birth"
    assert event.payload["registry_status"] == "draft"
    assert event.payload["registry_version"] == 1


def test_factory_merges_detached_attributes_without_mutating_input():
    attributes = {"repository": "memory"}
    event = make_factory().registered(
        make_registry(), metadata=metadata(), attributes=attributes
    )
    attributes["repository"] = "changed"
    assert event.payload["repository"] == "memory"


def test_factory_creates_status_changed_event_from_real_lifecycle_result():
    result = RegistryLifecycle().transition(make_registry(), RegistryStatus.ACTIVE)
    event = make_factory().status_changed(
        result,
        metadata=metadata(),
        reason=" approved activation ",
    )
    assert event.registry_event_type is RegistryEventType.REGISTRY_STATUS_CHANGED
    assert event.payload["previous_status"] == "draft"
    assert event.payload["current_status"] == "active"
    assert event.payload["reason"] == "approved activation"
    assert event.payload["registry_version"] == 2


def test_factory_rejects_noop_lifecycle_result():
    registry = make_registry()
    result = RegistryLifecycle().transition(registry, RegistryStatus.DRAFT)
    with pytest.raises(ValueError, match="no-op"):
        make_factory().status_changed(result, metadata=metadata())


def test_factory_validates_injected_dependencies_at_call_time():
    with pytest.raises(ValueError, match="event_id_factory"):
        RegistryEventFactory(
            event_id_factory=lambda: " ", clock=lambda: NOW
        ).registered(make_registry(), metadata=metadata())

    with pytest.raises(ValueError, match="timezone-aware"):
        RegistryEventFactory(
            event_id_factory=lambda: "evt", clock=lambda: datetime(2026, 7, 27)
        ).registered(make_registry(), metadata=metadata())
