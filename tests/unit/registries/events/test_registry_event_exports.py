import registries.events as events


def test_registry_event_public_exports_are_complete():
    assert set(events.__all__) == {
        "Clock",
        "EventIdFactory",
        "RegistryEvent",
        "RegistryEventFactory",
        "RegistryEventType",
    }
    for name in events.__all__:
        assert hasattr(events, name)
