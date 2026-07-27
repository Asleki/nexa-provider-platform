"""
============================================================
Nexa Provider Platform
File: tests/unit/events/repositories/test_event_repository_metadata.py
Layer: Shared Event Repository Tests
Milestone: NPP-M006.3.9 — Event Repository Metadata
============================================================

Unit tests for immutable event-repository metadata records,
metadata validation, metadata serialization, the metadata registry,
and built-in memory-repository metadata.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from shared.events.repositories.event_repository_errors import (
    EventAlreadyRegisteredError,
    EventNotRegisteredError,
    EventRegistrationError,
    EventRepositoryConfigurationError,
)
from shared.events.repositories.event_repository_metadata import (
    DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY,
    MEMORY_EVENT_REPOSITORY_METADATA,
    EventRepositoryMetadata,
    EventRepositoryMetadataRegistry,
)
from shared.events.repositories.event_repository_types import (
    EventRepositoryType,
)


def make_metadata(
    repository_type: str = "custom",
    **overrides,
) -> EventRepositoryMetadata:
    """Create valid metadata with optional field overrides."""

    values = {
        "repository_type": repository_type,
        "display_name": "Custom Repository",
        "description": "Repository used by metadata unit tests.",
        "persistent": False,
        "thread_safe": True,
        "ordering_guarantee": "Insertion order",
        "intended_uses": ("testing", "development"),
        "production_ready": False,
        "supports_delete": True,
        "supports_clear": True,
        "durable": False,
        "transactional": False,
        "metadata": {"provider": "unit_test"},
    }
    values.update(overrides)
    return EventRepositoryMetadata(**values)


def test_metadata_creation_preserves_valid_values():
    metadata = make_metadata()

    assert metadata.repository_type == "custom"
    assert metadata.display_name == "Custom Repository"
    assert metadata.description == "Repository used by metadata unit tests."
    assert metadata.persistent is False
    assert metadata.thread_safe is True
    assert metadata.ordering_guarantee == "Insertion order"
    assert metadata.intended_uses == ("testing", "development")
    assert metadata.production_ready is False
    assert metadata.supports_delete is True
    assert metadata.supports_clear is True
    assert metadata.durable is False
    assert metadata.transactional is False


def test_repository_type_is_normalized():
    metadata = make_metadata("  CUSTOM_BACKEND  ")

    assert metadata.repository_type == "custom_backend"


def test_repository_type_accepts_enum():
    metadata = make_metadata(EventRepositoryType.MEMORY)

    assert metadata.repository_type == EventRepositoryType.MEMORY.value


@pytest.mark.parametrize(
    "field_name, raw_value, expected",
    [
        ("display_name", "  Custom Repository  ", "Custom Repository"),
        (
            "description",
            "  Repository description.  ",
            "Repository description.",
        ),
        (
            "ordering_guarantee",
            "  Event ID order  ",
            "Event ID order",
        ),
    ],
)
def test_required_strings_are_trimmed(field_name, raw_value, expected):
    metadata = make_metadata(**{field_name: raw_value})

    assert getattr(metadata, field_name) == expected


@pytest.mark.parametrize(
    "field_name",
    [
        "display_name",
        "description",
        "ordering_guarantee",
    ],
)
@pytest.mark.parametrize("raw_value", ["", " ", "\n\t"])
def test_empty_required_strings_are_rejected(field_name, raw_value):
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(**{field_name: raw_value})


@pytest.mark.parametrize(
    "field_name, raw_value",
    [
        ("display_name", None),
        ("description", 42),
        ("ordering_guarantee", object()),
    ],
)
def test_non_string_required_fields_are_rejected(field_name, raw_value):
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(**{field_name: raw_value})


def test_intended_uses_are_trimmed_and_deduplicated_in_order():
    metadata = make_metadata(
        intended_uses=(
            " testing ",
            "development",
            "testing",
            " simulation ",
            "development",
        )
    )

    assert metadata.intended_uses == (
        "testing",
        "development",
        "simulation",
    )


def test_intended_uses_accepts_general_iterable_and_freezes_to_tuple():
    metadata = make_metadata(
        intended_uses=["testing", "simulation"]
    )

    assert metadata.intended_uses == ("testing", "simulation")
    assert isinstance(metadata.intended_uses, tuple)


@pytest.mark.parametrize("raw_value", ["testing", b"testing"])
def test_intended_uses_rejects_string_and_bytes(raw_value):
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(intended_uses=raw_value)


def test_intended_uses_rejects_non_iterable():
    with pytest.raises(EventRepositoryConfigurationError) as exc_info:
        make_metadata(intended_uses=123)

    assert isinstance(exc_info.value.__cause__, TypeError)


@pytest.mark.parametrize(
    "raw_value",
    [
        (),
        [],
        iter(()),
    ],
)
def test_intended_uses_must_not_be_empty(raw_value):
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(intended_uses=raw_value)


def test_intended_uses_rejects_empty_member():
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(intended_uses=("testing", " "))


def test_intended_uses_rejects_non_string_member():
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(intended_uses=("testing", 123))


@pytest.mark.parametrize(
    "field_name",
    [
        "persistent",
        "thread_safe",
        "production_ready",
        "supports_delete",
        "supports_clear",
        "durable",
        "transactional",
    ],
)
@pytest.mark.parametrize("invalid_value", [0, 1, "true", None])
def test_boolean_fields_require_actual_bool(field_name, invalid_value):
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(**{field_name: invalid_value})


def test_metadata_requires_mapping():
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(metadata=[("provider", "unit_test")])


def test_durable_repository_must_be_persistent():
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(
            persistent=False,
            durable=True,
        )


def test_production_ready_repository_must_be_durable():
    with pytest.raises(EventRepositoryConfigurationError):
        make_metadata(
            persistent=True,
            durable=False,
            production_ready=True,
        )


def test_valid_production_ready_repository_is_accepted():
    metadata = make_metadata(
        persistent=True,
        durable=True,
        production_ready=True,
        transactional=True,
    )

    assert metadata.persistent is True
    assert metadata.durable is True
    assert metadata.production_ready is True
    assert metadata.transactional is True


def test_metadata_mapping_is_copied_and_frozen():
    source = {"provider": "original"}
    metadata = make_metadata(metadata=source)

    source["provider"] = "changed"

    assert metadata.metadata["provider"] == "original"
    assert isinstance(metadata.metadata, MappingProxyType)

    with pytest.raises(TypeError):
        metadata.metadata["provider"] = "mutated"


def test_dataclass_is_frozen():
    metadata = make_metadata()

    with pytest.raises(FrozenInstanceError):
        metadata.display_name = "Changed"


def test_to_dict_returns_plain_serializable_structures():
    metadata = make_metadata(
        intended_uses=("testing", "simulation"),
        metadata={"provider": "unit_test"},
    )

    result = metadata.to_dict()

    assert isinstance(result, dict)
    assert result["repository_type"] == "custom"
    assert result["intended_uses"] == ["testing", "simulation"]
    assert isinstance(result["intended_uses"], list)
    assert result["metadata"] == {"provider": "unit_test"}
    assert isinstance(result["metadata"], dict)


def test_to_dict_returns_independent_collections():
    metadata = make_metadata(
        intended_uses=("testing",),
        metadata={"provider": "unit_test"},
    )

    result = metadata.to_dict()
    result["intended_uses"].append("changed")
    result["metadata"]["provider"] = "changed"

    assert metadata.intended_uses == ("testing",)
    assert metadata.metadata["provider"] == "unit_test"


def test_registry_starts_empty():
    registry = EventRepositoryMetadataRegistry()

    assert registry.count == 0
    assert len(registry) == 0
    assert registry.registered_types == ()
    assert registry.list_all() == ()


def test_registry_registers_metadata():
    registry = EventRepositoryMetadataRegistry()
    metadata = make_metadata()

    registry.register(metadata)

    assert registry.count == 1
    assert registry.get("custom") is metadata


def test_registry_rejects_non_metadata_instance():
    registry = EventRepositoryMetadataRegistry()

    with pytest.raises(EventRepositoryConfigurationError):
        registry.register(object())


def test_registry_rejects_duplicate_registration():
    registry = EventRepositoryMetadataRegistry()
    metadata = make_metadata()

    registry.register(metadata)

    with pytest.raises(EventAlreadyRegisteredError):
        registry.register(make_metadata())


def test_registry_replace_overwrites_existing_metadata():
    registry = EventRepositoryMetadataRegistry()
    first = make_metadata(display_name="First")
    second = make_metadata(display_name="Second")

    registry.register(first)
    registry.register(second, replace=True)

    assert registry.count == 1
    assert registry.get("custom") is second
    assert registry.get("custom").display_name == "Second"


def test_registry_wraps_unexpected_registration_failure():
    class FailingDictionary(dict):
        def __setitem__(self, key, value):
            raise RuntimeError("storage failure")

    registry = EventRepositoryMetadataRegistry()
    registry._metadata = FailingDictionary()

    with pytest.raises(EventRegistrationError) as exc_info:
        registry.register(make_metadata())

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_registry_get_accepts_enum():
    registry = EventRepositoryMetadataRegistry()
    registry.register(MEMORY_EVENT_REPOSITORY_METADATA)

    result = registry.get(EventRepositoryType.MEMORY)

    assert result is MEMORY_EVENT_REPOSITORY_METADATA


def test_registry_get_normalizes_string():
    registry = EventRepositoryMetadataRegistry()
    metadata = make_metadata("custom")

    registry.register(metadata)

    assert registry.get("  CUSTOM  ") is metadata


def test_registry_get_missing_raises_not_registered():
    registry = EventRepositoryMetadataRegistry()

    with pytest.raises(EventNotRegisteredError) as exc_info:
        registry.get("missing")

    assert isinstance(exc_info.value.__cause__, KeyError)


def test_registry_unregister_returns_removed_metadata():
    registry = EventRepositoryMetadataRegistry()
    metadata = make_metadata()
    registry.register(metadata)

    removed = registry.unregister("custom")

    assert removed is metadata
    assert registry.count == 0
    assert not registry.is_registered("custom")


def test_registry_unregister_missing_raises_not_registered():
    registry = EventRepositoryMetadataRegistry()

    with pytest.raises(EventNotRegisteredError) as exc_info:
        registry.unregister("missing")

    assert isinstance(exc_info.value.__cause__, KeyError)


def test_registry_is_registered_normalizes_type():
    registry = EventRepositoryMetadataRegistry()
    registry.register(make_metadata("custom"))

    assert registry.is_registered(" CUSTOM ") is True
    assert registry.is_registered("missing") is False


def test_registered_types_are_sorted_deterministically():
    registry = EventRepositoryMetadataRegistry()
    registry.register(make_metadata("zeta"))
    registry.register(make_metadata("alpha"))
    registry.register(make_metadata("middle"))

    assert registry.registered_types == (
        "alpha",
        "middle",
        "zeta",
    )


def test_list_all_uses_deterministic_type_order():
    registry = EventRepositoryMetadataRegistry()
    zeta = make_metadata("zeta")
    alpha = make_metadata("alpha")
    middle = make_metadata("middle")

    registry.register(zeta)
    registry.register(alpha)
    registry.register(middle)

    assert registry.list_all() == (
        alpha,
        middle,
        zeta,
    )


def test_registry_contains_registered_enum_and_string():
    registry = EventRepositoryMetadataRegistry()
    registry.register(MEMORY_EVENT_REPOSITORY_METADATA)

    assert EventRepositoryType.MEMORY in registry
    assert "memory" in registry


def test_registry_contains_returns_false_for_invalid_object():
    registry = EventRepositoryMetadataRegistry()

    assert object() not in registry
    assert 123 not in registry
    assert None not in registry


def test_registry_contains_returns_false_for_invalid_string():
    registry = EventRepositoryMetadataRegistry()

    assert "" not in registry
    assert "   " not in registry


def test_registry_iteration_returns_sorted_type_names():
    registry = EventRepositoryMetadataRegistry()
    registry.register(make_metadata("zeta"))
    registry.register(make_metadata("alpha"))

    assert list(registry) == ["alpha", "zeta"]


def test_registry_clear_removes_all_metadata():
    registry = EventRepositoryMetadataRegistry()
    registry.register(make_metadata("alpha"))
    registry.register(make_metadata("beta"))

    registry.clear()

    assert registry.count == 0
    assert len(registry) == 0
    assert registry.registered_types == ()


def test_memory_metadata_has_expected_repository_type():
    assert (
        MEMORY_EVENT_REPOSITORY_METADATA.repository_type
        == EventRepositoryType.MEMORY.value
    )


def test_memory_metadata_has_expected_capabilities():
    metadata = MEMORY_EVENT_REPOSITORY_METADATA

    assert metadata.persistent is False
    assert metadata.thread_safe is True
    assert metadata.production_ready is False
    assert metadata.supports_delete is True
    assert metadata.supports_clear is True
    assert metadata.durable is False
    assert metadata.transactional is False


def test_memory_metadata_declares_expected_uses():
    assert MEMORY_EVENT_REPOSITORY_METADATA.intended_uses == (
        "testing",
        "simulation",
        "development",
        "early_integration",
    )


def test_default_metadata_registry_contains_memory_metadata():
    assert DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY.is_registered(
        EventRepositoryType.MEMORY
    )
    assert (
        DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY.get(
            EventRepositoryType.MEMORY
        )
        is MEMORY_EVENT_REPOSITORY_METADATA
    )


def test_default_metadata_registry_has_at_least_memory_registration():
    assert DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY.count >= 1
    assert (
        EventRepositoryType.MEMORY.value
        in DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY.registered_types
    )


def test_module_exports_expected_symbols():
    import shared.events.repositories.event_repository_metadata as module

    assert module.__all__ == [
        "EventRepositoryMetadata",
        "EventRepositoryMetadataRegistry",
        "MEMORY_EVENT_REPOSITORY_METADATA",
        "DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY",
    ]
