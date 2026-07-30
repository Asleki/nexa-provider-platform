from __future__ import annotations

import pytest

from registries.name_suggestions import (
    ManualNameComponentNotFoundError,
    ManualNameEntry,
    ManualNameEntryService,
)
from registries.names import FirstName, MemoryNameRepository, MiddleName, NameMetadata, Surname


def _repository() -> MemoryNameRepository:
    repository = MemoryNameRepository()
    repository.add(FirstName("name:first:tariro", "Tariro").as_canonical())
    repository.add(MiddleName("name:middle:rudo", "Rudo").as_canonical())
    repository.add(Surname("name:surname:ncube", "Ncube").as_canonical())
    repository.add(
        FirstName(
            "name:first:tariro:production",
            "Tariro",
            NameMetadata(runtime_mode="production"),
        ).as_canonical()
    )
    return repository


def test_service_resolves_single_name_case_insensitively() -> None:
    result = ManualNameEntryService(_repository()).resolve(
        ManualNameEntry(first_name="tArIrO")
    )

    assert result.rendered_value == "Tariro"
    assert result.component_ids == ("name:first:tariro",)
    assert result.runtime_mode == "simulation"


def test_service_resolves_pair_and_preserves_catalogue_ids() -> None:
    result = ManualNameEntryService(_repository()).resolve(
        ManualNameEntry(first_name="Tariro", surname="Ncube")
    )

    assert result.rendered_value == "Tariro Ncube"
    assert result.component_ids == (
        "name:first:tariro",
        "name:surname:ncube",
    )


def test_service_resolves_trio() -> None:
    result = ManualNameEntryService(_repository()).resolve(
        ManualNameEntry(first_name="Tariro", middle_name="Rudo", surname="Ncube")
    )

    assert result.rendered_value == "Tariro Rudo Ncube"
    assert result.component_count == 3


def test_service_enforces_runtime_isolation_and_does_not_mutate_catalogue() -> None:
    repository = _repository()
    service = ManualNameEntryService(repository)
    before = repository.count()

    result = service.resolve(
        ManualNameEntry(first_name="Tariro", runtime_mode="production")
    )

    assert result.component_ids == ("name:first:tariro:production",)
    assert repository.count() == before


def test_service_rejects_unknown_component_without_catalogue_mutation() -> None:
    repository = _repository()
    service = ManualNameEntryService(repository)
    before = repository.count()

    with pytest.raises(ManualNameComponentNotFoundError, match="Unknown"):
        service.resolve(ManualNameEntry(first_name="Unknown"))

    assert repository.count() == before
