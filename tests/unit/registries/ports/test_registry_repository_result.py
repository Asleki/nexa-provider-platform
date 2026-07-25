from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from registries.core.base_registry import BaseRegistry
from registries.core.registry_definition import RegistryDefinition
from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus
from registries.ports.registry_repository_result import (
    RegistryRepositoryResult,
)
from registries.ports.registry_repository_types import (
    RegistryRepositoryOperation,
)


def make_registry(registry_id: str = "registry-one") -> BaseRegistry:
    return BaseRegistry(
        RegistryDefinition(
            registry_id=registry_id,
            registry_code=registry_id.replace("registry-", ""),
            registry_name="Registry",
            family=RegistryFamily.CORE_INFRASTRUCTURE,
            status=RegistryStatus.ACTIVE,
        )
    )


def test_added_result_preserves_typed_registry() -> None:
    registry = make_registry()
    result = RegistryRepositoryResult.added(
        repository="registries",
        registry=registry,
    )
    assert result.operation is RegistryRepositoryOperation.ADD
    assert result.registry is registry
    assert result.registry_id == registry.registry_id
    assert result.count == 1


def test_list_result_preserves_order_and_count() -> None:
    first = make_registry("registry-one")
    second = make_registry("registry-two")
    result = RegistryRepositoryResult.listed(
        repository="registries",
        registries=(first, second),
    )
    assert result.registries == (first, second)
    assert result.count == 2


def test_metadata_is_defensively_copied_and_frozen() -> None:
    metadata = {"source": "test"}
    result = RegistryRepositoryResult.counted(
        repository="registries",
        count=2,
        metadata=metadata,
    )
    metadata["source"] = "changed"
    assert isinstance(result.metadata, MappingProxyType)
    assert result.metadata["source"] == "test"
    assert result.metadata["count"] == 2


def test_result_is_frozen() -> None:
    result = RegistryRepositoryResult.counted(
        repository="registries",
        count=0,
    )
    with pytest.raises(FrozenInstanceError):
        result.repository = "changed"  # type: ignore[misc]


def test_rejects_non_registry_values() -> None:
    with pytest.raises(TypeError, match="BaseRegistry"):
        RegistryRepositoryResult(
            success=True,
            operation=RegistryRepositoryOperation.READ,
            repository="registries",
            registry=object(),  # type: ignore[arg-type]
        )


def test_serialization_detaches_registry_data() -> None:
    registry = make_registry()
    result = RegistryRepositoryResult.found(
        repository="registries",
        registry=registry,
    )
    data = result.to_dict()
    assert data["registry"]["registry_id"] == registry.registry_id
    assert data["operation"] == "read"


@pytest.mark.parametrize("count", [-1, True, 1.5])
def test_counted_rejects_invalid_counts(count) -> None:
    with pytest.raises((TypeError, ValueError)):
        RegistryRepositoryResult.counted(
            repository="registries",
            count=count,  # type: ignore[arg-type]
        )
