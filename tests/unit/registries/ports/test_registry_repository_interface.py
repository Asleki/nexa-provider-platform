import inspect

import pytest

from registries.ports.registry_repository import (
    RegistryRepositoryInterface,
)


EXPECTED_ABSTRACT_METHODS = {
    "repository_name",
    "repository_type",
    "add",
    "get",
    "replace",
    "remove",
    "list_all",
    "exists",
    "count",
    "clear",
}


def test_interface_is_abstract() -> None:
    assert inspect.isabstract(RegistryRepositoryInterface)
    assert RegistryRepositoryInterface.__abstractmethods__ == (
        EXPECTED_ABSTRACT_METHODS
    )


def test_interface_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        RegistryRepositoryInterface()


def test_interface_uses_complete_object_replace_not_partial_update() -> None:
    assert not hasattr(RegistryRepositoryInterface, "update")
    assert hasattr(RegistryRepositoryInterface, "replace")
