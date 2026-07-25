import registries.factories as package


def test_factory_package_exports_are_exact_and_unique():
    expected = {
        "DEFAULT_REGISTRY_REPOSITORY_TYPE",
        "RegistryRepositoryAlreadyRegisteredError",
        "RegistryRepositoryClass",
        "RegistryRepositoryConstructionError",
        "RegistryRepositoryFactory",
        "RegistryRepositoryFactoryConfigurationError",
        "RegistryRepositoryNotRegisteredError",
        "RegistryRepositoryRegistrationError",
        "RegistryRepositoryRegistry",
        "normalize_registry_repository_type",
    }
    assert set(package.__all__) == expected
    assert len(package.__all__) == len(set(package.__all__))
    for name in package.__all__:
        assert hasattr(package, name)


def test_later_m008_symbols_are_not_exported():
    forbidden = {
        "RegistryCatalogue", "RegistryLifecycle", "RegistryValidator",
        "RegistryEventPublisher", "RegistryAuditService", "RegistryAPI",
    }
    assert forbidden.isdisjoint(package.__all__)


def test_memory_adapter_remains_owned_by_adapter_package():
    assert "MemoryRegistryRepository" not in package.__all__
