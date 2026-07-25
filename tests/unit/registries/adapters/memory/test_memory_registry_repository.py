from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from registries.adapters.memory import MemoryRegistryRepository
from registries.core.base_registry import BaseRegistry
from registries.core.registry_definition import RegistryDefinition
from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus
from registries.ports.base_registry_repository import BaseRegistryRepository
from registries.ports.registry_repository import RegistryRepositoryInterface
from registries.ports.registry_repository_errors import (
    RegistryDuplicateError,
    RegistryIdentifierError,
    RegistryInvalidRecordError,
    RegistryNotFoundError,
)
from registries.ports.registry_repository_types import RegistryRepositoryOperation


def make_registry(
    registry_id: str,
    *,
    name: str | None = None,
    version: int = 1,
) -> BaseRegistry:
    return BaseRegistry(
        RegistryDefinition(
            registry_id=registry_id,
            registry_code=registry_id.replace("registry-", ""),
            registry_name=name or registry_id,
            family=RegistryFamily.CORE_INFRASTRUCTURE,
            status=RegistryStatus.ACTIVE,
            version=version,
        )
    )


def test_repository_implements_approved_contracts() -> None:
    repository = MemoryRegistryRepository()
    assert isinstance(repository, BaseRegistryRepository)
    assert isinstance(repository, RegistryRepositoryInterface)
    assert repository.repository_name == "memory_registry_repository"
    assert repository.repository_type == "memory"


def test_custom_repository_name_is_normalized() -> None:
    assert (
        MemoryRegistryRepository(" Registry Memory ").repository_name
        == "Registry Memory"
    )


def test_add_and_get_preserve_exact_registry_object() -> None:
    repository = MemoryRegistryRepository()
    registry = make_registry("registry-one")
    added = repository.add(registry)
    found = repository.get(" registry-one ")
    assert added.operation is RegistryRepositoryOperation.ADD
    assert found.operation is RegistryRepositoryOperation.READ
    assert added.registry is registry
    assert found.registry is registry
    assert added.metadata["repository_type"] == "memory"


def test_duplicate_add_does_not_overwrite() -> None:
    repository = MemoryRegistryRepository()
    first = make_registry("registry-one", name="First")
    repository.add(first)
    with pytest.raises(RegistryDuplicateError):
        repository.add(make_registry("registry-one", name="Duplicate"))
    assert repository.get("registry-one").registry is first
    assert repository.count().records_affected == 1


def test_invalid_registry_and_identifier_are_rejected() -> None:
    repository = MemoryRegistryRepository()
    with pytest.raises(RegistryInvalidRecordError):
        repository.add(object())  # type: ignore[arg-type]
    with pytest.raises(RegistryIdentifierError):
        repository.get("   ")


def test_missing_get_raises_not_found() -> None:
    with pytest.raises(RegistryNotFoundError):
        MemoryRegistryRepository().get("missing")


def test_replace_requires_existing_record_and_preserves_order() -> None:
    repository = MemoryRegistryRepository()
    repository.add(make_registry("registry-one", name="Original"))
    repository.add(make_registry("registry-two"))
    replacement = make_registry("registry-one", name="Replacement", version=2)
    result = repository.replace(replacement)
    assert result.operation is RegistryRepositoryOperation.REPLACE
    assert repository.get("registry-one").registry is replacement
    assert repository.count().records_affected == 2
    assert tuple(
        registry.registry_id
        for registry in repository.list_all().registries
    ) == ("registry-one", "registry-two")


def test_replace_missing_record_is_rejected() -> None:
    with pytest.raises(RegistryNotFoundError):
        MemoryRegistryRepository().replace(make_registry("missing"))


def test_remove_and_missing_remove_behaviour() -> None:
    repository = MemoryRegistryRepository()
    repository.add(make_registry("registry-one"))
    removed = repository.remove(" registry-one ")
    assert removed.operation is RegistryRepositoryOperation.REMOVE
    assert repository.exists("registry-one").metadata["exists"] is False
    with pytest.raises(RegistryNotFoundError):
        repository.remove("registry-one")


def test_empty_and_ordered_list_snapshots() -> None:
    repository = MemoryRegistryRepository()
    assert repository.list_all().registries == ()
    first = make_registry("registry-one")
    second = make_registry("registry-two")
    third = make_registry("registry-three")
    repository.add(first)
    repository.add(second)
    snapshot = repository.list_all()
    repository.add(third)
    assert snapshot.registries == (first, second)
    assert repository.list_all().registries == (first, second, third)


def test_exists_reports_boolean_metadata() -> None:
    repository = MemoryRegistryRepository()
    repository.add(make_registry("registry-one"))
    assert repository.exists("registry-one").metadata["exists"] is True
    assert repository.exists("registry-two").metadata["exists"] is False


def test_count_tracks_all_operations() -> None:
    repository = MemoryRegistryRepository()
    assert repository.count().records_affected == 0
    repository.add(make_registry("registry-one"))
    repository.add(make_registry("registry-two"))
    assert repository.count().records_affected == 2
    repository.replace(make_registry("registry-one", version=2))
    assert repository.count().records_affected == 2
    repository.remove("registry-two")
    assert repository.count().records_affected == 1
    assert repository.clear().records_affected == 1
    assert repository.clear().records_affected == 0


def test_repository_instances_are_isolated() -> None:
    first = MemoryRegistryRepository()
    second = MemoryRegistryRepository()
    first.add(make_registry("registry-one"))
    assert first.count().records_affected == 1
    assert second.count().records_affected == 0


def test_concurrent_unique_adds_lose_no_records() -> None:
    repository = MemoryRegistryRepository()
    total = 80
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(
            executor.map(
                lambda index: repository.add(
                    make_registry(f"registry-{index:03d}")
                ),
                range(total),
            )
        )
    assert repository.count().records_affected == total
    assert len(repository.list_all().registries) == total


def test_concurrent_duplicate_add_has_one_success() -> None:
    repository = MemoryRegistryRepository()
    workers = 20
    barrier = Barrier(workers)

    def attempt() -> str:
        barrier.wait()
        try:
            repository.add(make_registry("registry-shared"))
            return "added"
        except RegistryDuplicateError:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=workers) as executor:
        outcomes = list(executor.map(lambda _: attempt(), range(workers)))
    assert outcomes.count("added") == 1
    assert outcomes.count("duplicate") == workers - 1
    assert repository.count().records_affected == 1


def test_concurrent_reads_and_lists_are_consistent() -> None:
    repository = MemoryRegistryRepository()
    for index in range(40):
        repository.add(make_registry(f"registry-{index:03d}"))

    def read(index: int) -> tuple[str, int]:
        registry = repository.get(f"registry-{index:03d}").registry
        assert registry is not None
        return registry.registry_id, len(repository.list_all().registries)

    with ThreadPoolExecutor(max_workers=10) as executor:
        outcomes = list(executor.map(read, range(40)))
    assert all(count == 40 for _, count in outcomes)
    assert len({registry_id for registry_id, _ in outcomes}) == 40
