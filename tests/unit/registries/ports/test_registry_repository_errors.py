from types import MappingProxyType

import pytest

from registries.ports.registry_repository_errors import (
    REGISTRY_REPOSITORY_ERROR_PREFIX,
    RegistryDuplicateError,
    RegistryIdentifierError,
    RegistryNotFoundError,
    RegistryRepositoryError,
    RegistryUnsupportedOperationError,
)
from registries.ports.registry_repository_types import (
    RegistryRepositoryOperation,
)


def test_base_error_preserves_structured_context() -> None:
    cause = OSError("backend failed")
    metadata = {"backend": "memory"}
    error = RegistryRepositoryError(
        " failed ",
        operation=RegistryRepositoryOperation.READ,
        repository=" registries ",
        registry_id=" registry-one ",
        repository_type=" memory ",
        cause=cause,
        metadata=metadata,
    )
    metadata["backend"] = "changed"

    assert error.message == "failed"
    assert error.operation == "read"
    assert error.repository == "registries"
    assert error.registry_id == "registry-one"
    assert error.repository_type == "memory"
    assert error.cause is cause
    assert isinstance(error.metadata, MappingProxyType)
    assert error.metadata["backend"] == "memory"


def test_error_serialization_is_deterministic() -> None:
    error = RegistryNotFoundError(
        "missing",
        operation="read",
        repository="registries",
        registry_id="registry-one",
    )
    data = error.to_dict()

    assert data["error"] == "RegistryNotFoundError"
    assert data["operation"] == "read"
    assert data["registry_id"] == "registry-one"
    assert data["error_code"].startswith(REGISTRY_REPOSITORY_ERROR_PREFIX)


@pytest.mark.parametrize(
    "error_type",
    [
        RegistryDuplicateError,
        RegistryIdentifierError,
        RegistryNotFoundError,
        RegistryUnsupportedOperationError,
    ],
)
def test_specialized_errors_remain_repository_errors(error_type) -> None:
    assert issubclass(error_type, RegistryRepositoryError)


def test_metadata_is_read_only() -> None:
    error = RegistryRepositoryError("failure", metadata={"key": "value"})
    with pytest.raises(TypeError):
        error.metadata["key"] = "changed"  # type: ignore[index]
