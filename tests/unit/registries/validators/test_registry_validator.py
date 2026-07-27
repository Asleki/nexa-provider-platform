
import pytest

from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily, RegistryStatus
from registries.validators import InvalidRegistryDefinitionError, RegistryValidator


def definition(**overrides):
    values = {
        "registry_id": "npp.registry.citizen",
        "registry_code": "CITIZEN",
        "registry_name": "Citizen Registry",
        "family": RegistryFamily.CORE_INFRASTRUCTURE,
        "status": RegistryStatus.DRAFT,
        "description": "Canonical citizen registry.",
        "version": 1,
        "metadata": {"owner": "npp"},
    }
    values.update(overrides)
    return RegistryDefinition(**values)


def codes(result):
    return {message.code for message in result.messages}


def test_valid_definition_and_base_registry_pass_without_mutation():
    item = definition()
    before = item.to_dict()
    result = RegistryValidator.validate(item)
    facade_result = RegistryValidator.validate(BaseRegistry(item))
    assert result.valid is True
    assert facade_result == result
    assert item.to_dict() == before


def test_duplicate_and_reserved_checks_are_repository_neutral():
    item = definition()
    result = RegistryValidator.validate(
        item,
        existing_registry_ids=[item.registry_id],
        existing_registry_codes=[item.registry_code.lower()],
        reserved_registry_codes=[item.registry_code],
    )
    assert {"REG-DEF-003", "REG-DEF-007", "REG-DEF-008"} <= codes(result)


def test_definition_policy_collects_multiple_findings():
    item = definition(
        registry_id="bad id",
        registry_code="A",
        registry_name="A",
        description="x" * 2001,
        metadata={"x" * 201: "value"},
    )
    result = RegistryValidator.validate(item)
    assert result.invalid
    assert {"REG-DEF-002", "REG-DEF-004", "REG-DEF-011", "REG-DEF-015"} <= codes(result)
    assert "REG-DEF-010" in codes(result)


def test_validate_or_raise_returns_result_or_raises_structured_error():
    valid = RegistryValidator.validate_or_raise(definition())
    assert valid.valid
    with pytest.raises(InvalidRegistryDefinitionError) as caught:
        RegistryValidator.validate_or_raise(definition(registry_id="bad id"))
    assert caught.value.result.invalid
    assert "REG-DEF-002" in codes(caught.value.result)


def test_validator_rejects_unapproved_inputs_and_bad_comparison_iterables():
    with pytest.raises(TypeError):
        RegistryValidator.validate({})
    with pytest.raises(TypeError):
        RegistryValidator.validate(definition(), existing_registry_ids="one-id")
    with pytest.raises(TypeError):
        RegistryValidator.validate(definition(), existing_registry_codes=[1])


def test_active_without_description_is_information_not_failure():
    item = definition(status=RegistryStatus.ACTIVE, description="")
    result = RegistryValidator.validate(item)
    assert result.valid
    assert "REG-DEF-012" in codes(result)
