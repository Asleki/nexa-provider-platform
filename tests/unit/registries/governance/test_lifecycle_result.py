from types import MappingProxyType

import pytest

from registries.core import (
    BaseRegistry,
    RegistryDefinition,
    RegistryFamily,
    RegistryStatus,
)
from registries.governance import RegistryLifecycleResult


def _registry(status=RegistryStatus.ACTIVE):
    return BaseRegistry(
        RegistryDefinition(
            registry_id="npp.registry.citizens",
            registry_code="CITIZENS",
            registry_name="Citizen Registry",
            family=RegistryFamily.CORE_INFRASTRUCTURE,
            status=status,
            metadata={"owner": "civil-registry"},
        )
    )


def test_result_is_immutable_and_serializable():
    registry = _registry()
    result = RegistryLifecycleResult(
        registry=registry,
        previous_status=RegistryStatus.ACTIVE,
        current_status=RegistryStatus.ACTIVE,
        changed=False,
        message=" no change ",
        metadata={"retry_safe": True},
    )
    assert result.registry_id == registry.registry_id
    assert result.status is RegistryStatus.ACTIVE
    assert result.noop is True
    assert result.message == "no change"
    assert isinstance(result.metadata, MappingProxyType)
    assert result.to_dict()["current_status"] == "active"
    with pytest.raises(Exception):
        result.changed = True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"registry": object()},
        {"previous_status": "active"},
        {"current_status": "active"},
        {"changed": 1},
        {"metadata": []},
    ],
)
def test_result_rejects_invalid_field_types(kwargs):
    values = {
        "registry": _registry(),
        "previous_status": RegistryStatus.ACTIVE,
        "current_status": RegistryStatus.ACTIVE,
        "changed": False,
    }
    values.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        RegistryLifecycleResult(**values)


def test_result_rejects_inconsistent_state():
    with pytest.raises(ValueError, match="registry.status"):
        RegistryLifecycleResult(
            registry=_registry(RegistryStatus.ACTIVE),
            previous_status=RegistryStatus.DRAFT,
            current_status=RegistryStatus.SUSPENDED,
            changed=True,
        )
    with pytest.raises(ValueError, match="statuses are equal"):
        RegistryLifecycleResult(
            registry=_registry(),
            previous_status=RegistryStatus.ACTIVE,
            current_status=RegistryStatus.ACTIVE,
            changed=True,
        )
