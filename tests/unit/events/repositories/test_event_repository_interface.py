"""
============================================================
Nexa Provider Platform
File: tests/unit/events/repositories/test_event_repository_interface_v001.py
Layer: Shared Event Repository Tests
Milestone: NPP-M006.3.1 — Event Repository Interface
============================================================

Unit tests for the storage-independent event repository
contract.

The suite verifies abstractness, exact public members, property
descriptors, method signatures, annotations, subclass
requirements, concrete implementation behavior, and module
exports.
"""

from __future__ import annotations

import inspect
from abc import ABC
from typing import get_type_hints

import pytest

from shared.events.event_envelope import EventEnvelope
from shared.events.repositories.event_repository_interface import (
    EventRepositoryInterface,
)
from shared.events.repositories.event_repository_result import (
    EventRepositoryResult,
)


EXPECTED_ABSTRACT_MEMBERS = {
    "repository_name",
    "repository_type",
    "store",
    "get",
    "list_all",
    "exists",
    "count",
    "delete",
    "clear",
}

EXPECTED_METHOD_PARAMETER_NAMES = {
    "store": ["self", "envelope"],
    "get": ["self", "event_id"],
    "list_all": ["self"],
    "exists": ["self", "event_id"],
    "count": ["self"],
    "delete": ["self", "event_id"],
    "clear": ["self"],
}


class CompleteRepository(EventRepositoryInterface):
    """Minimal concrete implementation used for contract tests."""

    @property
    def repository_name(self) -> str:
        return "complete_repository"

    @property
    def repository_type(self) -> str:
        return "test"

    def store(
        self,
        envelope: EventEnvelope,
    ) -> EventRepositoryResult:
        return EventRepositoryResult.success(
            operation="store",
            repository_name=self.repository_name,
            repository_type=self.repository_type,
            event=envelope,
        )

    def get(
        self,
        event_id: str,
    ) -> EventRepositoryResult:
        return EventRepositoryResult.success(
            operation="read",
            repository_name=self.repository_name,
            repository_type=self.repository_type,
            event_id=event_id,
        )

    def list_all(self) -> EventRepositoryResult:
        return EventRepositoryResult.success(
            operation="list",
            repository_name=self.repository_name,
            repository_type=self.repository_type,
            events=(),
        )

    def exists(
        self,
        event_id: str,
    ) -> EventRepositoryResult:
        return EventRepositoryResult.success(
            operation="exists",
            repository_name=self.repository_name,
            repository_type=self.repository_type,
            event_id=event_id,
            exists=False,
        )

    def count(self) -> EventRepositoryResult:
        return EventRepositoryResult.success(
            operation="count",
            repository_name=self.repository_name,
            repository_type=self.repository_type,
            count=0,
        )

    def delete(
        self,
        event_id: str,
    ) -> EventRepositoryResult:
        return EventRepositoryResult.success(
            operation="delete",
            repository_name=self.repository_name,
            repository_type=self.repository_type,
            event_id=event_id,
        )

    def clear(self) -> EventRepositoryResult:
        return EventRepositoryResult.success(
            operation="clear",
            repository_name=self.repository_name,
            repository_type=self.repository_type,
            count=0,
        )


def _build_partial_subclass(missing_member: str) -> type[EventRepositoryInterface]:
    """
    Build a subclass implementing every abstract member except one.

    The generated class lets each abstract requirement be tested in
    isolation without coupling the test to a real repository backend.
    """

    namespace: dict[str, object] = {}

    if missing_member != "repository_name":
        namespace["repository_name"] = property(
            lambda self: "partial_repository"
        )

    if missing_member != "repository_type":
        namespace["repository_type"] = property(
            lambda self: "test"
        )

    if missing_member != "store":
        namespace["store"] = lambda self, envelope: None

    if missing_member != "get":
        namespace["get"] = lambda self, event_id: None

    if missing_member != "list_all":
        namespace["list_all"] = lambda self: None

    if missing_member != "exists":
        namespace["exists"] = lambda self, event_id: None

    if missing_member != "count":
        namespace["count"] = lambda self: None

    if missing_member != "delete":
        namespace["delete"] = lambda self, event_id: None

    if missing_member != "clear":
        namespace["clear"] = lambda self: None

    return type(
        f"Missing{missing_member.title().replace('_', '')}Repository",
        (EventRepositoryInterface,),
        namespace,
    )


def test_event_repository_interface_is_class():
    assert inspect.isclass(EventRepositoryInterface)


def test_event_repository_interface_inherits_from_abc():
    assert issubclass(EventRepositoryInterface, ABC)


def test_event_repository_interface_is_abstract():
    assert inspect.isabstract(EventRepositoryInterface)


def test_event_repository_interface_cannot_be_instantiated_directly():
    with pytest.raises(TypeError, match="abstract"):
        EventRepositoryInterface()


def test_event_repository_interface_has_exact_abstract_members():
    assert EventRepositoryInterface.__abstractmethods__ == (
        EXPECTED_ABSTRACT_MEMBERS
    )


def test_event_repository_interface_defines_exact_contract_members():
    public_contract_members = {
        name
        for name in EventRepositoryInterface.__dict__
        if not name.startswith("_")
    }

    assert public_contract_members == EXPECTED_ABSTRACT_MEMBERS


@pytest.mark.parametrize(
    "property_name",
    [
        "repository_name",
        "repository_type",
    ],
)
def test_repository_metadata_member_is_property(property_name):
    descriptor = EventRepositoryInterface.__dict__[property_name]

    assert isinstance(descriptor, property)


@pytest.mark.parametrize(
    "property_name",
    [
        "repository_name",
        "repository_type",
    ],
)
def test_repository_metadata_property_has_getter(property_name):
    descriptor = EventRepositoryInterface.__dict__[property_name]

    assert descriptor.fget is not None


@pytest.mark.parametrize(
    "property_name",
    [
        "repository_name",
        "repository_type",
    ],
)
def test_repository_metadata_property_has_no_setter(property_name):
    descriptor = EventRepositoryInterface.__dict__[property_name]

    assert descriptor.fset is None


@pytest.mark.parametrize(
    "property_name",
    [
        "repository_name",
        "repository_type",
    ],
)
def test_repository_metadata_property_has_no_deleter(property_name):
    descriptor = EventRepositoryInterface.__dict__[property_name]

    assert descriptor.fdel is None


@pytest.mark.parametrize(
    "property_name",
    [
        "repository_name",
        "repository_type",
    ],
)
def test_repository_metadata_property_is_abstract(property_name):
    descriptor = EventRepositoryInterface.__dict__[property_name]

    assert descriptor.__isabstractmethod__ is True
    assert descriptor.fget.__isabstractmethod__ is True


@pytest.mark.parametrize(
    "property_name",
    [
        "repository_name",
        "repository_type",
    ],
)
def test_repository_metadata_property_return_annotation_is_str(
    property_name,
):
    descriptor = EventRepositoryInterface.__dict__[property_name]
    hints = get_type_hints(descriptor.fget)

    assert hints["return"] is str


@pytest.mark.parametrize(
    "method_name",
    [
        "store",
        "get",
        "list_all",
        "exists",
        "count",
        "delete",
        "clear",
    ],
)
def test_repository_operation_is_function(method_name):
    member = EventRepositoryInterface.__dict__[method_name]

    assert inspect.isfunction(member)


@pytest.mark.parametrize(
    "method_name",
    [
        "store",
        "get",
        "list_all",
        "exists",
        "count",
        "delete",
        "clear",
    ],
)
def test_repository_operation_is_abstract(method_name):
    member = EventRepositoryInterface.__dict__[method_name]

    assert member.__isabstractmethod__ is True


@pytest.mark.parametrize(
    "method_name, expected_parameter_names",
    EXPECTED_METHOD_PARAMETER_NAMES.items(),
)
def test_repository_operation_parameter_names_and_order(
    method_name,
    expected_parameter_names,
):
    signature = inspect.signature(
        EventRepositoryInterface.__dict__[method_name]
    )

    assert list(signature.parameters) == expected_parameter_names


@pytest.mark.parametrize(
    "method_name",
    [
        "store",
        "get",
        "list_all",
        "exists",
        "count",
        "delete",
        "clear",
    ],
)
def test_repository_operation_has_no_variadic_parameters(method_name):
    signature = inspect.signature(
        EventRepositoryInterface.__dict__[method_name]
    )

    assert all(
        parameter.kind
        not in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }
        for parameter in signature.parameters.values()
    )


@pytest.mark.parametrize(
    "method_name",
    [
        "store",
        "get",
        "list_all",
        "exists",
        "count",
        "delete",
        "clear",
    ],
)
def test_repository_operation_parameters_have_no_defaults(method_name):
    signature = inspect.signature(
        EventRepositoryInterface.__dict__[method_name]
    )

    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )


@pytest.mark.parametrize(
    "method_name",
    [
        "store",
        "get",
        "list_all",
        "exists",
        "count",
        "delete",
        "clear",
    ],
)
def test_repository_operation_returns_event_repository_result(method_name):
    method = EventRepositoryInterface.__dict__[method_name]
    hints = get_type_hints(
        method,
        globalns={
            **method.__globals__,
            "EventRepositoryResult": EventRepositoryResult,
        },
    )

    assert hints["return"] is EventRepositoryResult


def test_store_envelope_annotation_is_event_envelope():
    hints = get_type_hints(
        EventRepositoryInterface.store,
        globalns={
            **EventRepositoryInterface.store.__globals__,
            "EventRepositoryResult": EventRepositoryResult,
        },
    )

    assert hints["envelope"] is EventEnvelope


@pytest.mark.parametrize(
    "method_name",
    [
        "get",
        "exists",
        "delete",
    ],
)
def test_event_id_parameter_annotation_is_str(method_name):
    method = EventRepositoryInterface.__dict__[method_name]
    hints = get_type_hints(
        method,
        globalns={
            **method.__globals__,
            "EventRepositoryResult": EventRepositoryResult,
        },
    )

    assert hints["event_id"] is str


@pytest.mark.parametrize(
    "method_name",
    [
        "list_all",
        "count",
        "clear",
    ],
)
def test_parameterless_operation_only_accepts_self(method_name):
    signature = inspect.signature(
        EventRepositoryInterface.__dict__[method_name]
    )

    assert tuple(signature.parameters) == ("self",)


def test_interface_deliberately_has_no_update_operation():
    assert "update" not in EventRepositoryInterface.__dict__
    assert not hasattr(EventRepositoryInterface, "update")


def test_interface_deliberately_has_no_save_alias():
    assert "save" not in EventRepositoryInterface.__dict__
    assert not hasattr(EventRepositoryInterface, "save")


def test_interface_deliberately_has_no_create_operation():
    assert "create" not in EventRepositoryInterface.__dict__
    assert not hasattr(EventRepositoryInterface, "create")


def test_complete_repository_is_not_abstract():
    assert not inspect.isabstract(CompleteRepository)


def test_complete_repository_can_be_instantiated():
    repository = CompleteRepository()

    assert isinstance(repository, CompleteRepository)
    assert isinstance(repository, EventRepositoryInterface)


def test_complete_repository_metadata_properties_are_accessible():
    repository = CompleteRepository()

    assert repository.repository_name == "complete_repository"
    assert repository.repository_type == "test"


def test_complete_repository_implements_all_contract_members():
    repository = CompleteRepository()

    for member_name in EXPECTED_ABSTRACT_MEMBERS:
        assert hasattr(repository, member_name)


@pytest.mark.parametrize(
    "missing_member",
    sorted(EXPECTED_ABSTRACT_MEMBERS),
)
def test_subclass_missing_one_contract_member_remains_abstract(
    missing_member,
):
    partial_subclass = _build_partial_subclass(missing_member)

    assert inspect.isabstract(partial_subclass)
    assert missing_member in partial_subclass.__abstractmethods__


@pytest.mark.parametrize(
    "missing_member",
    sorted(EXPECTED_ABSTRACT_MEMBERS),
)
def test_subclass_missing_one_contract_member_cannot_be_instantiated(
    missing_member,
):
    partial_subclass = _build_partial_subclass(missing_member)

    with pytest.raises(TypeError, match="abstract"):
        partial_subclass()


def test_inherited_abstract_members_are_satisfied_by_complete_subclass():
    assert CompleteRepository.__abstractmethods__ == frozenset()


def test_concrete_property_override_does_not_need_property_setter():
    repository = CompleteRepository()

    with pytest.raises(AttributeError):
        repository.repository_name = "changed"

    with pytest.raises(AttributeError):
        repository.repository_type = "changed"


def test_interface_class_name_is_stable():
    assert EventRepositoryInterface.__name__ == (
        "EventRepositoryInterface"
    )


def test_interface_qualname_is_stable():
    assert EventRepositoryInterface.__qualname__ == (
        "EventRepositoryInterface"
    )


def test_interface_module_path_is_stable():
    assert EventRepositoryInterface.__module__ == (
        "shared.events.repositories.event_repository_interface"
    )


def test_interface_docstring_describes_immutable_persistence():
    docstring = inspect.getdoc(EventRepositoryInterface)

    assert docstring is not None
    assert "immutable EventEnvelope persistence" in docstring


def test_interface_docstring_states_no_update_operation():
    docstring = inspect.getdoc(EventRepositoryInterface)

    assert docstring is not None
    assert "no update operation" in docstring


@pytest.mark.parametrize(
    "member_name",
    sorted(EXPECTED_ABSTRACT_MEMBERS),
)
def test_each_contract_member_has_docstring(member_name):
    member = EventRepositoryInterface.__dict__[member_name]

    if isinstance(member, property):
        docstring = inspect.getdoc(member.fget)
    else:
        docstring = inspect.getdoc(member)

    assert docstring


def test_module_exports_exact_public_contract():
    import shared.events.repositories.event_repository_interface as module

    assert module.__all__ == [
        "EventRepositoryInterface",
    ]


def test_exported_interface_resolves_to_expected_class():
    import shared.events.repositories.event_repository_interface as module

    assert module.EventRepositoryInterface is EventRepositoryInterface


def test_wildcard_import_exports_only_interface():
    namespace: dict[str, object] = {}

    exec(
        "from shared.events.repositories.event_repository_interface import *",
        {},
        namespace,
    )

    exported_names = {
        name
        for name in namespace
        if not name.startswith("__")
    }

    assert exported_names == {
        "EventRepositoryInterface",
    }
