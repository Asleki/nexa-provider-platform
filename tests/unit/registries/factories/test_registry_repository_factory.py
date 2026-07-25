import pytest

from registries.adapters.memory.memory_registry_repository import MemoryRegistryRepository
from registries.factories.registry_repository_factory import (
    DEFAULT_REGISTRY_REPOSITORY_TYPE,
    RegistryRepositoryFactory,
)
from registries.factories.registry_repository_factory_errors import (
    RegistryRepositoryConstructionError,
    RegistryRepositoryFactoryConfigurationError,
    RegistryRepositoryNotRegisteredError,
)
from registries.factories.registry_repository_registry import RegistryRepositoryRegistry
from registries.ports.registry_repository import RegistryRepositoryInterface


class CustomMemoryRepository(MemoryRegistryRepository):
    def __init__(self, token: str, *, repository_name: str = "custom") -> None:
        super().__init__(repository_name=repository_name)
        self.token = token


class BrokenRepository(MemoryRegistryRepository):
    def __init__(self) -> None:
        raise RuntimeError("construction failed")


def test_default_factory_registers_and_creates_memory_repository():
    factory = RegistryRepositoryFactory()
    assert DEFAULT_REGISTRY_REPOSITORY_TYPE == "memory"
    assert factory.registry.is_registered("memory")
    repository = factory.create()
    assert isinstance(repository, MemoryRegistryRepository)
    assert isinstance(repository, RegistryRepositoryInterface)


def test_factory_creates_fresh_instances_and_forwards_repository_name():
    factory = RegistryRepositoryFactory()
    first = factory.create(" MEMORY ", repository_name="first")
    second = factory.create_memory("second")
    assert first is not second
    assert first.repository_name == "first"
    assert second.repository_name == "second"


def test_injected_registry_and_constructor_arguments_are_supported():
    registry = RegistryRepositoryRegistry()
    registry.register("custom", CustomMemoryRepository)
    factory = RegistryRepositoryFactory(registry, register_defaults=False)
    repository = factory.create("custom", "secret", repository_name="named")
    assert isinstance(repository, CustomMemoryRepository)
    assert repository.token == "secret"
    assert repository.repository_name == "named"


def test_register_defaults_is_idempotent_and_preserves_injected_override():
    registry = RegistryRepositoryRegistry()
    registry.register("memory", CustomMemoryRepository)
    factory = RegistryRepositoryFactory(registry)
    factory.register_defaults()
    assert registry.get("memory") is CustomMemoryRepository


def test_defaults_can_be_disabled():
    factory = RegistryRepositoryFactory(register_defaults=False)
    assert factory.registry.registered_types == ()
    with pytest.raises(RegistryRepositoryNotRegisteredError):
        factory.create()


@pytest.mark.parametrize("registry", [object(), {}, "registry"])
def test_invalid_injected_registry_is_rejected(registry):
    with pytest.raises(RegistryRepositoryFactoryConfigurationError):
        RegistryRepositoryFactory(registry)


@pytest.mark.parametrize("value", [1, None, "yes"])
def test_register_defaults_must_be_boolean(value):
    with pytest.raises(RegistryRepositoryFactoryConfigurationError):
        RegistryRepositoryFactory(register_defaults=value)


def test_constructor_failure_is_wrapped_with_context_and_cause():
    registry = RegistryRepositoryRegistry()
    registry.register("broken", BrokenRepository)
    factory = RegistryRepositoryFactory(registry, register_defaults=False)
    with pytest.raises(RegistryRepositoryConstructionError) as exc_info:
        factory.create("broken")
    error = exc_info.value
    assert error.repository_type == "broken"
    assert isinstance(error.cause, RuntimeError)
    assert error.metadata["repository_class"] == "BrokenRepository"


def test_create_memory_rejects_non_memory_override():
    registry = RegistryRepositoryRegistry()
    registry.register("memory", CustomMemoryRepository)
    factory = RegistryRepositoryFactory(registry)
    with pytest.raises(RegistryRepositoryConstructionError):
        factory.create_memory()
