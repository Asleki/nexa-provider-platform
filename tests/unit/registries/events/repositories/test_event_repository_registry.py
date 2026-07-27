"""
============================================================
Nexa Provider Platform
File: tests/unit/events/repositories/test_event_repository_registry.py
Layer: Shared Event Repository Tests
Milestone: NPP-M006.3.7 — Event Repository Registry
============================================================

Unit tests for EventRepositoryRegistry and repository-type
normalization.

This test module verifies registration, replacement, lookup,
unregistration, deterministic iteration, membership behavior,
validation, and registry reuse.
"""

from __future__ import annotations

import pytest

from shared.events.repositories.event_repository_errors import (
    EventAlreadyRegisteredError,
    EventNotRegisteredError,
    EventRepositoryConfigurationError,
)
from shared.events.repositories.event_repository_registry import (
    EventRepositoryRegistry,
    normalize_event_repository_type,
)
from shared.events.repositories.event_repository_types import (
    EventRepositoryType,
)
from shared.events.repositories.memory_event_repository import (
    MemoryEventRepository,
)


class AlternateMemoryEventRepository(MemoryEventRepository):
    """Second valid concrete repository class for replacement tests."""


class UnrelatedClass:
    """Class that deliberately does not implement the repository interface."""


def test_normalize_repository_type_from_enum() -> None:
    assert (
        normalize_event_repository_type(EventRepositoryType.MEMORY)
        == EventRepositoryType.MEMORY.value
    )


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("memory", "memory"),
        (" MEMORY ", "memory"),
        ("Future_Backend", "future_backend"),
        ("  custom-repository  ", "custom-repository"),
    ],
)
def test_normalize_repository_type_from_string(
    raw_value: str,
    expected: str,
) -> None:
    assert normalize_event_repository_type(raw_value) == expected


@pytest.mark.parametrize("raw_value", ["", " ", "\t", "\n"])
def test_normalize_repository_type_rejects_empty_string(
    raw_value: str,
) -> None:
    with pytest.raises(EventRepositoryConfigurationError):
        normalize_event_repository_type(raw_value)


def test_new_registry_is_empty() -> None:
    registry = EventRepositoryRegistry()

    assert registry.count == 0
    assert len(registry) == 0
    assert registry.registered_types == ()
    assert tuple(registry) == ()


def test_register_accepts_enum_repository_type() -> None:
    registry = EventRepositoryRegistry()

    registry.register(
        EventRepositoryType.MEMORY,
        MemoryEventRepository,
    )

    assert registry.get(EventRepositoryType.MEMORY) is MemoryEventRepository


def test_register_accepts_future_string_repository_type() -> None:
    registry = EventRepositoryRegistry()

    registry.register(
        "future_database",
        MemoryEventRepository,
    )

    assert registry.get("future_database") is MemoryEventRepository


def test_register_normalizes_string_repository_type() -> None:
    registry = EventRepositoryRegistry()

    registry.register(
        "  MEMORY  ",
        MemoryEventRepository,
    )

    assert registry.get("memory") is MemoryEventRepository
    assert registry.registered_types == ("memory",)


def test_register_rejects_non_class_value() -> None:
    registry = EventRepositoryRegistry()

    with pytest.raises(
        EventRepositoryConfigurationError,
        match="repository_class must be a class",
    ):
        registry.register(
            "memory",
            MemoryEventRepository(),
        )


def test_register_rejects_unrelated_class() -> None:
    registry = EventRepositoryRegistry()

    with pytest.raises(
        EventRepositoryConfigurationError,
        match="EventRepositoryInterface",
    ):
        registry.register(
            "unrelated",
            UnrelatedClass,
        )


def test_register_rejects_duplicate_type_by_default() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    with pytest.raises(
        EventAlreadyRegisteredError,
        match="already registered",
    ):
        registry.register(
            " MEMORY ",
            AlternateMemoryEventRepository,
        )


def test_duplicate_registration_preserves_original_class() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    with pytest.raises(EventAlreadyRegisteredError):
        registry.register(
            "memory",
            AlternateMemoryEventRepository,
        )

    assert registry.get("memory") is MemoryEventRepository


def test_register_replace_true_replaces_existing_class() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    registry.register(
        "memory",
        AlternateMemoryEventRepository,
        replace=True,
    )

    assert registry.get("memory") is AlternateMemoryEventRepository
    assert registry.count == 1


def test_get_returns_registered_class() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    repository_class = registry.get("memory")

    assert repository_class is MemoryEventRepository


def test_get_normalizes_repository_type() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    assert registry.get(" MEMORY ") is MemoryEventRepository


def test_get_raises_for_missing_registration() -> None:
    registry = EventRepositoryRegistry()

    with pytest.raises(
        EventNotRegisteredError,
        match="not registered",
    ):
        registry.get("missing")


def test_get_missing_registration_preserves_key_error_cause() -> None:
    registry = EventRepositoryRegistry()

    with pytest.raises(EventNotRegisteredError) as exc_info:
        registry.get("missing")

    assert isinstance(exc_info.value.__cause__, KeyError)


def test_unregister_returns_removed_repository_class() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    removed_class = registry.unregister("memory")

    assert removed_class is MemoryEventRepository
    assert registry.count == 0


def test_unregister_normalizes_repository_type() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    removed_class = registry.unregister(" MEMORY ")

    assert removed_class is MemoryEventRepository


def test_unregister_raises_for_missing_registration() -> None:
    registry = EventRepositoryRegistry()

    with pytest.raises(
        EventNotRegisteredError,
        match="not registered",
    ):
        registry.unregister("missing")


def test_unregister_missing_registration_preserves_key_error_cause() -> None:
    registry = EventRepositoryRegistry()

    with pytest.raises(EventNotRegisteredError) as exc_info:
        registry.unregister("missing")

    assert isinstance(exc_info.value.__cause__, KeyError)


def test_is_registered_returns_true_for_registered_type() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    assert registry.is_registered("memory") is True


def test_is_registered_returns_false_for_missing_type() -> None:
    registry = EventRepositoryRegistry()

    assert registry.is_registered("missing") is False


def test_is_registered_normalizes_repository_type() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    assert registry.is_registered(" MEMORY ") is True


def test_contains_supports_enum_and_string_types() -> None:
    registry = EventRepositoryRegistry()
    registry.register(EventRepositoryType.MEMORY, MemoryEventRepository)

    assert EventRepositoryType.MEMORY in registry
    assert "memory" in registry
    assert " MEMORY " in registry


@pytest.mark.parametrize(
    "invalid_value",
    [None, 123, 3.14, object(), MemoryEventRepository],
)
def test_contains_returns_false_for_unsupported_values(
    invalid_value: object,
) -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    assert invalid_value not in registry


@pytest.mark.parametrize("empty_value", ["", " ", "\t"])
def test_contains_returns_false_for_empty_repository_type(
    empty_value: str,
) -> None:
    registry = EventRepositoryRegistry()

    assert empty_value not in registry


def test_registered_types_are_sorted_deterministically() -> None:
    registry = EventRepositoryRegistry()
    registry.register("zeta", MemoryEventRepository)
    registry.register("alpha", MemoryEventRepository)
    registry.register("middle", MemoryEventRepository)

    assert registry.registered_types == (
        "alpha",
        "middle",
        "zeta",
    )


def test_iteration_uses_sorted_registered_types() -> None:
    registry = EventRepositoryRegistry()
    registry.register("zeta", MemoryEventRepository)
    registry.register("alpha", MemoryEventRepository)
    registry.register("middle", MemoryEventRepository)

    assert tuple(registry) == (
        "alpha",
        "middle",
        "zeta",
    )


def test_count_and_len_track_registry_size() -> None:
    registry = EventRepositoryRegistry()

    assert registry.count == 0
    assert len(registry) == 0

    registry.register("memory", MemoryEventRepository)
    registry.register("future", AlternateMemoryEventRepository)

    assert registry.count == 2
    assert len(registry) == 2


def test_clear_removes_all_registrations() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)
    registry.register("future", AlternateMemoryEventRepository)

    registry.clear()

    assert registry.count == 0
    assert len(registry) == 0
    assert registry.registered_types == ()
    assert tuple(registry) == ()
    assert "memory" not in registry
    assert "future" not in registry


def test_clear_empty_registry_is_safe() -> None:
    registry = EventRepositoryRegistry()

    registry.clear()
    registry.clear()

    assert registry.count == 0


def test_registry_can_reuse_type_after_unregister() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)
    registry.unregister("memory")

    registry.register(
        "memory",
        AlternateMemoryEventRepository,
    )

    assert registry.get("memory") is AlternateMemoryEventRepository


def test_registry_can_reuse_type_after_clear() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)
    registry.clear()

    registry.register(
        "memory",
        AlternateMemoryEventRepository,
    )

    assert registry.get("memory") is AlternateMemoryEventRepository


def test_registered_types_returns_immutable_tuple() -> None:
    registry = EventRepositoryRegistry()
    registry.register("memory", MemoryEventRepository)

    registered_types = registry.registered_types

    assert isinstance(registered_types, tuple)

    with pytest.raises(AttributeError):
        registered_types.append("future")  # type: ignore[attr-defined]


def test_registry_stores_classes_without_instantiating_them() -> None:
    registry = EventRepositoryRegistry()

    registry.register("memory", MemoryEventRepository)

    stored_value = registry.get("memory")

    assert stored_value is MemoryEventRepository
    assert isinstance(stored_value, type)
