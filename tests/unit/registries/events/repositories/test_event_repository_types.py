"""
============================================================
Nexa Provider Platform
File: tests/unit/events/repositories/test_event_repository_types.py
Layer: Shared Event Repository Tests
Milestone: NPP-M006.3.11 — Event Repository Types
============================================================

Unit tests for the stable event-repository operation and
implementation type identifiers.
"""

from __future__ import annotations

import json
from enum import Enum

import pytest

from shared.events.repositories.event_repository_types import (
    EventRepositoryOperation,
    EventRepositoryType,
)


EXPECTED_OPERATION_MEMBERS = {
    "STORE": "store",
    "READ": "read",
    "DELETE": "delete",
    "LIST": "list",
    "EXISTS": "exists",
    "COUNT": "count",
    "CLEAR": "clear",
}

EXPECTED_REPOSITORY_TYPE_MEMBERS = {
    "MEMORY": "memory",
}


def test_event_repository_operation_is_enum_subclass():
    assert issubclass(EventRepositoryOperation, Enum)


def test_event_repository_operation_is_string_subclass():
    assert issubclass(EventRepositoryOperation, str)


def test_event_repository_operation_members_are_strings():
    for member in EventRepositoryOperation:
        assert isinstance(member, str)


def test_event_repository_operation_contains_exact_expected_members():
    assert EventRepositoryOperation.__members__ == {
        name: EventRepositoryOperation(value)
        for name, value in EXPECTED_OPERATION_MEMBERS.items()
    }


def test_event_repository_operation_member_names_are_exact():
    assert [member.name for member in EventRepositoryOperation] == [
        "STORE",
        "READ",
        "DELETE",
        "LIST",
        "EXISTS",
        "COUNT",
        "CLEAR",
    ]


def test_event_repository_operation_member_values_are_exact():
    assert [member.value for member in EventRepositoryOperation] == [
        "store",
        "read",
        "delete",
        "list",
        "exists",
        "count",
        "clear",
    ]


def test_event_repository_operation_declaration_order_is_stable():
    assert list(EventRepositoryOperation) == [
        EventRepositoryOperation.STORE,
        EventRepositoryOperation.READ,
        EventRepositoryOperation.DELETE,
        EventRepositoryOperation.LIST,
        EventRepositoryOperation.EXISTS,
        EventRepositoryOperation.COUNT,
        EventRepositoryOperation.CLEAR,
    ]


@pytest.mark.parametrize(
    "member_name, expected_value",
    EXPECTED_OPERATION_MEMBERS.items(),
)
def test_event_repository_operation_name_lookup(
    member_name,
    expected_value,
):
    member = EventRepositoryOperation[member_name]

    assert member.name == member_name
    assert member.value == expected_value


@pytest.mark.parametrize(
    "member_name, member_value",
    EXPECTED_OPERATION_MEMBERS.items(),
)
def test_event_repository_operation_value_lookup_returns_same_singleton(
    member_name,
    member_value,
):
    assert EventRepositoryOperation(member_value) is getattr(
        EventRepositoryOperation,
        member_name,
    )


@pytest.mark.parametrize(
    "member_name, member_value",
    EXPECTED_OPERATION_MEMBERS.items(),
)
def test_event_repository_operation_compares_equal_to_string_value(
    member_name,
    member_value,
):
    member = getattr(EventRepositoryOperation, member_name)

    assert member == member_value
    assert member_value == member


@pytest.mark.parametrize(
    "member_name, member_value",
    EXPECTED_OPERATION_MEMBERS.items(),
)
def test_event_repository_operation_hash_matches_string_value(
    member_name,
    member_value,
):
    member = getattr(EventRepositoryOperation, member_name)

    assert hash(member) == hash(member_value)


@pytest.mark.parametrize(
    "member_name, member_value",
    EXPECTED_OPERATION_MEMBERS.items(),
)
def test_event_repository_operation_can_be_used_as_string_dict_key(
    member_name,
    member_value,
):
    member = getattr(EventRepositoryOperation, member_name)
    mapping = {member: member_name}

    assert mapping[member_value] == member_name


@pytest.mark.parametrize(
    "member_name, member_value",
    EXPECTED_OPERATION_MEMBERS.items(),
)
def test_event_repository_operation_json_serializes_as_string_value(
    member_name,
    member_value,
):
    member = getattr(EventRepositoryOperation, member_name)

    assert json.dumps(member) == json.dumps(member_value)


def test_event_repository_operation_list_json_serialization():
    serialized = json.dumps(list(EventRepositoryOperation))

    assert json.loads(serialized) == list(
        EXPECTED_OPERATION_MEMBERS.values()
    )


def test_event_repository_operation_values_are_unique():
    values = [member.value for member in EventRepositoryOperation]

    assert len(values) == len(set(values))


def test_event_repository_operation_names_are_unique():
    names = [member.name for member in EventRepositoryOperation]

    assert len(names) == len(set(names))


def test_event_repository_operation_has_no_aliases():
    assert len(EventRepositoryOperation.__members__) == len(
        list(EventRepositoryOperation)
    )


def test_event_repository_operation_has_no_update_member():
    assert "UPDATE" not in EventRepositoryOperation.__members__
    assert not hasattr(EventRepositoryOperation, "UPDATE")


@pytest.mark.parametrize(
    "invalid_value",
    [
        "update",
        "STORE",
        "Read",
        "",
        " ",
        None,
        1,
        object(),
    ],
)
def test_event_repository_operation_rejects_invalid_value(invalid_value):
    with pytest.raises(ValueError):
        EventRepositoryOperation(invalid_value)


@pytest.mark.parametrize(
    "invalid_name",
    [
        "UPDATE",
        "store",
        "Read",
        "",
        "UNKNOWN",
    ],
)
def test_event_repository_operation_rejects_invalid_name(invalid_name):
    with pytest.raises(KeyError):
        EventRepositoryOperation[invalid_name]


def test_event_repository_operation_length_is_seven():
    assert len(EventRepositoryOperation) == 7


def test_event_repository_operation_iteration_is_repeatable():
    first_pass = list(EventRepositoryOperation)
    second_pass = list(EventRepositoryOperation)

    assert first_pass == second_pass


def test_event_repository_operation_members_are_singletons():
    for member in EventRepositoryOperation:
        assert EventRepositoryOperation(member.value) is member
        assert EventRepositoryOperation[member.name] is member


def test_event_repository_operation_member_repr_identifies_enum():
    representation = repr(EventRepositoryOperation.STORE)

    assert "EventRepositoryOperation.STORE" in representation
    assert "'store'" in representation


def test_event_repository_operation_member_name_is_read_only():
    with pytest.raises(AttributeError):
        EventRepositoryOperation.STORE.name = "CHANGED"


def test_event_repository_operation_member_value_is_read_only():
    with pytest.raises(AttributeError):
        EventRepositoryOperation.STORE.value = "changed"


def test_event_repository_type_is_enum_subclass():
    assert issubclass(EventRepositoryType, Enum)


def test_event_repository_type_is_string_subclass():
    assert issubclass(EventRepositoryType, str)


def test_event_repository_type_members_are_strings():
    for member in EventRepositoryType:
        assert isinstance(member, str)


def test_event_repository_type_contains_exact_expected_members():
    assert EventRepositoryType.__members__ == {
        "MEMORY": EventRepositoryType.MEMORY,
    }


def test_event_repository_type_member_names_are_exact():
    assert [member.name for member in EventRepositoryType] == [
        "MEMORY",
    ]


def test_event_repository_type_member_values_are_exact():
    assert [member.value for member in EventRepositoryType] == [
        "memory",
    ]


def test_event_repository_type_declaration_order_is_stable():
    assert list(EventRepositoryType) == [
        EventRepositoryType.MEMORY,
    ]


def test_event_repository_type_name_lookup():
    assert EventRepositoryType["MEMORY"] is EventRepositoryType.MEMORY


def test_event_repository_type_value_lookup():
    assert EventRepositoryType("memory") is EventRepositoryType.MEMORY


def test_event_repository_type_compares_equal_to_string_value():
    assert EventRepositoryType.MEMORY == "memory"
    assert "memory" == EventRepositoryType.MEMORY


def test_event_repository_type_hash_matches_string_value():
    assert hash(EventRepositoryType.MEMORY) == hash("memory")


def test_event_repository_type_can_be_used_as_string_dict_key():
    mapping = {EventRepositoryType.MEMORY: "repository"}

    assert mapping["memory"] == "repository"


def test_event_repository_type_json_serializes_as_string_value():
    assert json.dumps(EventRepositoryType.MEMORY) == '"memory"'


def test_event_repository_type_values_are_unique():
    values = [member.value for member in EventRepositoryType]

    assert len(values) == len(set(values))


def test_event_repository_type_names_are_unique():
    names = [member.name for member in EventRepositoryType]

    assert len(names) == len(set(names))


def test_event_repository_type_has_no_aliases():
    assert len(EventRepositoryType.__members__) == len(
        list(EventRepositoryType)
    )


def test_event_repository_type_length_is_one():
    assert len(EventRepositoryType) == 1


@pytest.mark.parametrize(
    "invalid_value",
    [
        "MEMORY",
        "database",
        "postgresql",
        "",
        " ",
        None,
        1,
        object(),
    ],
)
def test_event_repository_type_rejects_invalid_value(invalid_value):
    with pytest.raises(ValueError):
        EventRepositoryType(invalid_value)


@pytest.mark.parametrize(
    "invalid_name",
    [
        "memory",
        "DATABASE",
        "POSTGRESQL",
        "",
        "UNKNOWN",
    ],
)
def test_event_repository_type_rejects_invalid_name(invalid_name):
    with pytest.raises(KeyError):
        EventRepositoryType[invalid_name]


def test_event_repository_type_memory_is_singleton():
    assert EventRepositoryType("memory") is EventRepositoryType.MEMORY
    assert EventRepositoryType["MEMORY"] is EventRepositoryType.MEMORY


def test_event_repository_type_member_repr_identifies_enum():
    representation = repr(EventRepositoryType.MEMORY)

    assert "EventRepositoryType.MEMORY" in representation
    assert "'memory'" in representation


def test_event_repository_type_member_name_is_read_only():
    with pytest.raises(AttributeError):
        EventRepositoryType.MEMORY.name = "CHANGED"


def test_event_repository_type_member_value_is_read_only():
    with pytest.raises(AttributeError):
        EventRepositoryType.MEMORY.value = "changed"


def test_operation_and_repository_type_are_distinct_enum_classes():
    assert EventRepositoryOperation is not EventRepositoryType


def test_operation_and_repository_type_members_are_not_interchangeable():
    assert EventRepositoryOperation.STORE != EventRepositoryType.MEMORY


def test_all_enum_values_are_lowercase_identifiers():
    values = [
        *(member.value for member in EventRepositoryOperation),
        *(member.value for member in EventRepositoryType),
    ]

    assert all(value == value.lower() for value in values)
    assert all(value.isidentifier() for value in values)


def test_module_exports_exact_public_contract():
    import shared.events.repositories.event_repository_types as module

    assert module.__all__ == [
        "EventRepositoryOperation",
        "EventRepositoryType",
    ]


def test_all_exported_names_resolve_to_expected_classes():
    import shared.events.repositories.event_repository_types as module

    assert module.EventRepositoryOperation is EventRepositoryOperation
    assert module.EventRepositoryType is EventRepositoryType


def test_wildcard_import_exports_only_declared_contract():
    namespace: dict[str, object] = {}

    exec(
        "from shared.events.repositories.event_repository_types import *",
        {},
        namespace,
    )

    exported_names = {
        name
        for name in namespace
        if not name.startswith("__")
    }

    assert exported_names == {
        "EventRepositoryOperation",
        "EventRepositoryType",
    }
