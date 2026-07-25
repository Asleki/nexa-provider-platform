from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from registries.core import IdentifierDefinition, IdentifierDefinitionError, RegistryStatus


def _model(**overrides):
    values = dict(
        identifier_id=" id.birth.ref ", registry_id=" registry.birth ",
        namespace_id=" namespace.civil ", identifier_code=" birth_ref ",
        identifier_name=" Birth Reference ", status="active",
        description=" Reference definition. ", pattern=r"BR-[0-9]+",
        prefix=" BR ", minimum_length=5, maximum_length=20,
        case_sensitive=False, version=1, metadata={" owner ": "civil"},
    )
    values.update(overrides)
    return IdentifierDefinition(**values)


def test_valid_construction_and_properties():
    model = _model()
    assert model.identifier_id == "id.birth.ref"
    assert model.identifier_code == "BIRTH_REF"
    assert model.status is RegistryStatus.ACTIVE
    assert model.description == "Reference definition."
    assert model.prefix == "BR"
    assert model.identity == ("id.birth.ref", "BIRTH_REF")
    assert model.ownership == ("registry.birth", "namespace.civil")
    assert model.qualified_code == "registry.birth:namespace.civil:BIRTH_REF"
    assert model.active and not model.inactive
    assert model.has_pattern and model.has_prefix and model.length_bounded
    assert model.allows_length(5) and not model.allows_length(21)


@pytest.mark.parametrize("field", ["identifier_id", "registry_id", "namespace_id", "identifier_code", "identifier_name"])
def test_required_text_validation(field):
    with pytest.raises(IdentifierDefinitionError, match=f"{field} cannot be empty"):
        _model(**{field: " "})
    with pytest.raises(TypeError, match=f"{field} must be text"):
        _model(**{field: 1})


def test_length_and_version_guards():
    with pytest.raises(IdentifierDefinitionError, match="minimum_length cannot exceed"):
        _model(minimum_length=10, maximum_length=5)
    for field in ("minimum_length", "maximum_length"):
        with pytest.raises(TypeError):
            _model(**{field: True})
        with pytest.raises(IdentifierDefinitionError):
            _model(**{field: 0})
    with pytest.raises(TypeError, match="version must be an integer"):
        _model(version=True)
    with pytest.raises(IdentifierDefinitionError, match="greater than or equal"):
        _model(version=0)


def test_metadata_is_copied_read_only_and_key_normalized():
    source = {" owner ": "civil"}
    model = _model(metadata=source)
    source[" owner "] = "changed"
    assert model.metadata == {"owner": "civil"}
    assert isinstance(model.metadata, MappingProxyType)
    with pytest.raises(TypeError):
        model.metadata["owner"] = "changed"
    with pytest.raises(TypeError, match="metadata keys must be text"):
        _model(metadata={1: "x"})
    with pytest.raises(IdentifierDefinitionError, match="metadata keys cannot be empty"):
        _model(metadata={" ": "x"})


def test_serialization_round_trip_is_strict_and_non_mutating():
    model = _model()
    payload = model.to_dict()
    before = dict(payload)
    assert IdentifierDefinition.from_dict(payload) == model
    assert payload == before
    with pytest.raises(TypeError, match="values must be a mapping"):
        IdentifierDefinition.from_dict([])
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        IdentifierDefinition.from_dict({**payload, "unknown": True})


def test_frozen_and_summary():
    model = _model()
    with pytest.raises(FrozenInstanceError):
        model.identifier_name = "Changed"
    assert "BIRTH_REF" in model.summary()
