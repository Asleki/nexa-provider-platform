from __future__ import annotations

import pytest

from registries.name_suggestions import ManualNameEntry


def test_manual_entry_normalizes_and_renders_trio() -> None:
    entry = ManualNameEntry(
        first_name="  tArIrO ",
        middle_name="  rUdO  ",
        surname=" nCuBe ",
        runtime_mode=" SIMULATION ",
    )

    assert entry.first_name == "tArIrO"
    assert entry.middle_name == "rUdO"
    assert entry.surname == "nCuBe"
    assert entry.runtime_mode == "simulation"
    assert entry.component_count == 3
    assert entry.rendered_value == "tArIrO rUdO nCuBe"


def test_manual_entry_allows_single_name() -> None:
    entry = ManualNameEntry(first_name="Tariro")

    assert entry.component_count == 1
    assert entry.rendered_value == "Tariro"


def test_manual_entry_treats_blank_optional_components_as_absent() -> None:
    entry = ManualNameEntry(first_name="Tariro", middle_name="  ", surname="")

    assert entry.middle_name is None
    assert entry.surname is None


def test_manual_entry_rejects_blank_first_name() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        ManualNameEntry(first_name="   ")
