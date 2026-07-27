from types import MappingProxyType

import pytest

from registries.core import RegistryStatus
from registries.errors import RegistryError, RegistryStateError
from registries.governance import (
    RegistryLifecycleError,
    RegistryLifecycleInputError,
    RegistryLifecycleTerminalStateError,
    RegistryLifecycleTransitionError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        RegistryLifecycleError,
        RegistryLifecycleInputError,
        RegistryLifecycleTransitionError,
        RegistryLifecycleTerminalStateError,
    ],
)
def test_lifecycle_errors_extend_shared_registry_error(error_type):
    assert issubclass(error_type, RegistryError)
    assert issubclass(error_type, RegistryStateError)


def test_lifecycle_error_preserves_normalized_diagnostics():
    error = RegistryLifecycleTransitionError(
        " denied ",
        registry_id=" npp.registry.citizens ",
        current_status=RegistryStatus.ACTIVE,
        target_status=" suspended ",
        field=" target_status ",
        context={"reason": "policy"},
    )
    assert error.message == "denied"
    assert error.registry_id == "npp.registry.citizens"
    assert error.current_status == "active"
    assert error.target_status == "suspended"
    assert error.field == "target_status"
    assert isinstance(error.context, MappingProxyType)
    assert error.context["reason"] == "policy"
    assert error.to_dict()["code"] == error.error_code


def test_specialized_errors_keep_expected_python_categories():
    assert issubclass(RegistryLifecycleInputError, ValueError)
    assert issubclass(RegistryLifecycleTransitionError, ValueError)
    assert issubclass(
        RegistryLifecycleTerminalStateError,
        RegistryLifecycleTransitionError,
    )


def test_lifecycle_error_codes_are_unique():
    types = [
        RegistryLifecycleError,
        RegistryLifecycleInputError,
        RegistryLifecycleTransitionError,
        RegistryLifecycleTerminalStateError,
    ]
    assert len({item.error_code for item in types}) == len(types)
