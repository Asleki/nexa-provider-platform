import pytest

from registries.adapters.memory.memory_registry_repository import MemoryRegistryRepository
from registries.factories.registry_repository_factory_errors import (
    RegistryRepositoryAlreadyRegisteredError,
    RegistryRepositoryFactoryConfigurationError,
    RegistryRepositoryNotRegisteredError,
)
from registries.factories.registry_repository_registry import (
    RegistryRepositoryRegistry,
    normalize_registry_repository_type,
)


class AlternateMemoryRegistryRepository(MemoryRegistryRepository):
    pass


@pytest.mark.parametrize("raw, expected", [
    ("memory", "memory"), (" MEMORY ", "memory"), ("Custom-Store", "custom-store")
])
def test_normalize_repository_type(raw, expected):
    assert normalize_registry_repository_type(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", None, 7, object()])
def test_normalize_rejects_invalid_repository_type(raw):
    with pytest.raises(RegistryRepositoryFactoryConfigurationError):
        normalize_registry_repository_type(raw)


def test_registry_registers_and_resolves_implementation():
    registry = RegistryRepositoryRegistry()
    registry.register(" MEMORY ", MemoryRegistryRepository)
    assert registry.get("memory") is MemoryRegistryRepository
    assert registry.is_registered(" Memory ")
    assert "memory" in registry
    assert len(registry) == 1


def test_registry_rejects_non_class_and_incompatible_class():
    registry = RegistryRepositoryRegistry()
    with pytest.raises(RegistryRepositoryFactoryConfigurationError):
        registry.register("memory", MemoryRegistryRepository())
    with pytest.raises(RegistryRepositoryFactoryConfigurationError):
        registry.register("memory", dict)


def test_duplicate_requires_explicit_replace():
    registry = RegistryRepositoryRegistry()
    registry.register("memory", MemoryRegistryRepository)
    with pytest.raises(RegistryRepositoryAlreadyRegisteredError):
        registry.register("memory", AlternateMemoryRegistryRepository)
    registry.register("memory", AlternateMemoryRegistryRepository, replace=True)
    assert registry.get("memory") is AlternateMemoryRegistryRepository


def test_unregister_returns_class_and_missing_type_is_controlled():
    registry = RegistryRepositoryRegistry()
    registry.register("memory", MemoryRegistryRepository)
    assert registry.unregister("memory") is MemoryRegistryRepository
    with pytest.raises(RegistryRepositoryNotRegisteredError) as exc_info:
        registry.get("memory")
    assert exc_info.value.repository_type == "memory"


def test_registered_types_iteration_count_and_clear_are_deterministic():
    registry = RegistryRepositoryRegistry()
    registry.register("zeta", MemoryRegistryRepository)
    registry.register("alpha", AlternateMemoryRegistryRepository)
    assert registry.registered_types == ("alpha", "zeta")
    assert tuple(registry) == ("alpha", "zeta")
    assert registry.count == 2
    registry.clear()
    assert registry.registered_types == ()
    assert len(registry) == 0


def test_contains_is_safe_for_invalid_values():
    registry = RegistryRepositoryRegistry()
    assert None not in registry
    assert " " not in registry
