import inspect

import pytest

from registries.core.base_registry import BaseRegistry
from registries.core.registry_definition import RegistryDefinition
from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus
from registries.ports.base_registry_repository import (
    BaseRegistryRepository,
)
from registries.ports.registry_repository_errors import (
    RegistryIdentifierError,
    RegistryInvalidRecordError,
    RegistryRepositoryConfigurationError,
)


class ProbeRepository(BaseRegistryRepository):
    def add(self, registry): raise NotImplementedError
    def get(self, registry_id): raise NotImplementedError
    def replace(self, registry): raise NotImplementedError
    def remove(self, registry_id): raise NotImplementedError
    def list_all(self): raise NotImplementedError
    def exists(self, registry_id): raise NotImplementedError
    def count(self): raise NotImplementedError
    def clear(self): raise NotImplementedError


def make_registry() -> BaseRegistry:
    return BaseRegistry(
        RegistryDefinition(
            registry_id="registry-one",
            registry_code="one",
            registry_name="Registry One",
            family=RegistryFamily.CORE_INFRASTRUCTURE,
            status=RegistryStatus.ACTIVE,
        )
    )


def test_base_repository_remains_abstract() -> None:
    assert inspect.isabstract(BaseRegistryRepository)


def test_metadata_is_normalized() -> None:
    repository = ProbeRepository(" Registries ", " MEMORY ")
    assert repository.repository_name == "Registries"
    assert repository.repository_type == "memory"


@pytest.mark.parametrize(
    ("name", "repository_type"),
    [
        ("", "memory"),
        ("registries", ""),
        (None, "memory"),
        ("registries", None),
    ],
)
def test_invalid_configuration_is_rejected(name, repository_type) -> None:
    with pytest.raises(RegistryRepositoryConfigurationError):
        ProbeRepository(name, repository_type)  # type: ignore[arg-type]


def test_registry_identifier_validation() -> None:
    repository = ProbeRepository("registries", "memory")
    assert repository.validate_registry_id(" registry-one ") == "registry-one"
    with pytest.raises(RegistryIdentifierError):
        repository.validate_registry_id("")
    with pytest.raises(RegistryIdentifierError):
        repository.validate_registry_id(123)


def test_registry_type_validation() -> None:
    repository = ProbeRepository("registries", "memory")
    registry = make_registry()
    assert repository.validate_registry(registry) is registry
    with pytest.raises(RegistryInvalidRecordError):
        repository.validate_registry(object())


def test_base_repository_contains_no_storage_state() -> None:
    repository = ProbeRepository("registries", "memory")
    assert set(vars(repository)) == {
        "_repository_name",
        "_repository_type",
    }
