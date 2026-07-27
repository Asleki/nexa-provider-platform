import registries.governance as governance


def test_governance_package_exports_only_m008_8_symbols():
    expected = {
        "RegistryLifecycle",
        "RegistryLifecycleError",
        "RegistryLifecycleInputError",
        "RegistryLifecyclePolicy",
        "RegistryLifecycleResult",
        "RegistryLifecycleTerminalStateError",
        "RegistryLifecycleTransitionError",
    }
    assert set(governance.__all__) == expected
    assert len(governance.__all__) == len(set(governance.__all__))
    for name in governance.__all__:
        assert hasattr(governance, name)


def test_future_governance_capabilities_are_not_exported():
    forbidden = {
        "RegistryValidator",
        "RegistryEventPublisher",
        "RegistryAuditService",
        "RegistryAPI",
        "IssuancePolicy",
        "RelationshipPolicy",
    }
    assert forbidden.isdisjoint(governance.__all__)
