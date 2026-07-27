from registries.events import RegistryEventType


def test_registry_event_type_values_are_stable_and_namespaced():
    assert tuple(item.value for item in RegistryEventType) == (
        "registry.registered",
        "registry.replaced",
        "registry.removed",
        "registry.status_changed",
    )


def test_registry_event_type_string_and_action_helpers():
    event_type = RegistryEventType.REGISTRY_STATUS_CHANGED
    assert str(event_type) == "registry.status_changed"
    assert event_type.action == "status_changed"
