from registries.adapters import memory
from registries.adapters.memory import MemoryRegistryRepository
from registries.ports import __all__ as port_exports


def test_memory_package_exports_are_exact() -> None:
    assert memory.__all__ == ["MemoryRegistryRepository"]
    assert memory.MemoryRegistryRepository is MemoryRegistryRepository


def test_concrete_repository_is_not_exported_from_ports() -> None:
    assert "MemoryRegistryRepository" not in port_exports


def test_future_components_are_not_exported() -> None:
    forbidden = {
        "RegistryRepositoryFactory",
        "RegistryCatalogue",
        "RegistryLifecycleService",
        "RegistryAuditService",
    }
    assert forbidden.isdisjoint(set(memory.__all__))
