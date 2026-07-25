from types import MappingProxyType

import pytest

from registries.factories.registry_repository_factory_errors import (
    RegistryRepositoryAlreadyRegisteredError,
    RegistryRepositoryConstructionError,
    RegistryRepositoryFactoryConfigurationError,
    RegistryRepositoryNotRegisteredError,
    RegistryRepositoryRegistrationError,
)
from registries.ports.registry_repository_errors import RegistryRepositoryError


@pytest.mark.parametrize("error_type", [
    RegistryRepositoryFactoryConfigurationError,
    RegistryRepositoryRegistrationError,
    RegistryRepositoryAlreadyRegisteredError,
    RegistryRepositoryNotRegisteredError,
    RegistryRepositoryConstructionError,
])
def test_factory_errors_extend_registry_repository_error(error_type):
    assert issubclass(error_type, RegistryRepositoryError)


def test_error_preserves_diagnostics_and_read_only_metadata():
    cause = RuntimeError("boom")
    error = RegistryRepositoryConstructionError(
        " failed ", repository_type=" memory ", cause=cause,
        metadata={"repository_class": "BrokenRepository"},
    )
    assert error.message == "failed"
    assert error.repository_type == "memory"
    assert error.cause is cause
    assert isinstance(error.metadata, MappingProxyType)
    assert error.to_dict()["cause"] == "RuntimeError"
    assert error.to_dict()["metadata"] == {"repository_class": "BrokenRepository"}


def test_specialized_errors_keep_expected_python_categories():
    assert issubclass(RegistryRepositoryFactoryConfigurationError, ValueError)
    assert issubclass(RegistryRepositoryAlreadyRegisteredError, ValueError)
    assert issubclass(RegistryRepositoryNotRegisteredError, LookupError)


def test_error_codes_are_unique():
    types = [
        RegistryRepositoryFactoryConfigurationError,
        RegistryRepositoryRegistrationError,
        RegistryRepositoryAlreadyRegisteredError,
        RegistryRepositoryNotRegisteredError,
        RegistryRepositoryConstructionError,
    ]
    assert len({item.error_code for item in types}) == len(types)
