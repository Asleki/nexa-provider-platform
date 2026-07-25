from types import MappingProxyType

import pytest

from registries.contracts.registry_contract import (
    RegistryContract,
    RegistryContractError,
)
from registries.core.registry_definition import RegistryDefinition
from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus


def _definition() -> RegistryDefinition:
    return RegistryDefinition(
        registry_id="npp.registry.providers",
        registry_code="providers",
        registry_name="Provider Registry",
        family=RegistryFamily.CORE_INFRASTRUCTURE,
        status=RegistryStatus.ACTIVE,
        description="Canonical provider registry definition.",
        metadata={"owner": "platform"},
    )


def test_registry_definition_satisfies_contract():
    definition = _definition()
    assert isinstance(definition, RegistryContract)
    assert RegistryContract.require(definition) is definition


def test_contract_exposes_required_definition_shape():
    definition = RegistryContract.require(_definition())
    assert definition.registry_id == "npp.registry.providers"
    assert definition.registry_code == "PROVIDERS"
    assert definition.registry_name == "Provider Registry"
    assert definition.family is RegistryFamily.CORE_INFRASTRUCTURE
    assert definition.status is RegistryStatus.ACTIVE
    assert definition.description
    assert definition.version == 1
    assert definition.metadata == {"owner": "platform"}
    assert definition.to_dict()["registry_code"] == "PROVIDERS"


@pytest.mark.parametrize(
    "value",
    [
        object(),
        {"registry_id": "npp.registry.providers"},
        None,
        "registry",
    ],
)
def test_non_conforming_values_are_rejected(value):
    with pytest.raises(
        RegistryContractError,
        match="must satisfy RegistryContract",
    ):
        RegistryContract.require(value)


def test_contract_check_does_not_mutate_definition():
    source_metadata = {"owner": "platform"}
    definition = RegistryDefinition(
        registry_id="npp.registry.providers",
        registry_code="providers",
        registry_name="Provider Registry",
        family=RegistryFamily.CORE_INFRASTRUCTURE,
        metadata=source_metadata,
    )
    before = definition.to_dict()

    RegistryContract.require(definition)

    assert definition.to_dict() == before
    assert isinstance(definition.metadata, MappingProxyType)
    assert source_metadata == {"owner": "platform"}
