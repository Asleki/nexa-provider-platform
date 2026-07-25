from dataclasses import FrozenInstanceError
from types import MappingProxyType
import pytest

from registries.core import IdentifierLifecycle, IdentifierReference, IdentifierReferenceError


def _model(**overrides):
    values = dict(
        reference_id=" ref-1 ", registry_id=" registry.birth ",
        namespace_id=" namespace.civil ", identifier_id=" id.birth.ref ",
        subject_reference=" subject-1 ", identifier_value=" BR-0001 ",
        status="active", source_reference=" event-1 ", version=1,
        metadata={" source ": "simulation"},
    )
    values.update(overrides)
    return IdentifierReference(**values)


def test_valid_construction_uses_identifier_lifecycle():
    model = _model()
    assert model.status is IdentifierLifecycle.ACTIVE
    assert model.active and not model.inactive
    assert model.identity == ("ref-1", "BR-0001")
    assert model.ownership == ("registry.birth", "namespace.civil", "id.birth.ref")
    assert model.sourced
    assert model.qualified_reference.endswith(":BR-0001")


def test_default_lifecycle_is_requested():
    model = _model(status=IdentifierLifecycle.REQUESTED)
    assert model.status is IdentifierLifecycle.REQUESTED


@pytest.mark.parametrize("field", ["reference_id", "registry_id", "namespace_id", "identifier_id", "subject_reference", "identifier_value"])
def test_required_text_validation(field):
    with pytest.raises(IdentifierReferenceError, match=f"{field} cannot be empty"):
        _model(**{field: " "})
    with pytest.raises(TypeError, match=f"{field} must be text"):
        _model(**{field: 1})


def test_unknown_lifecycle_and_version_are_rejected():
    with pytest.raises(IdentifierReferenceError, match="Unsupported identifier-reference status"):
        _model(status="draft")
    with pytest.raises(TypeError, match="version must be an integer"):
        _model(version=True)
    with pytest.raises(IdentifierReferenceError, match="greater than or equal"):
        _model(version=0)


def test_metadata_and_serialization_are_immutable_and_strict():
    source = {" source ": "simulation"}
    model = _model(metadata=source)
    source[" source "] = "changed"
    assert model.metadata == {"source": "simulation"}
    assert isinstance(model.metadata, MappingProxyType)
    payload = model.to_dict()
    before = dict(payload)
    assert IdentifierReference.from_dict(payload) == model
    assert payload == before
    with pytest.raises(TypeError, match="values must be a mapping"):
        IdentifierReference.from_dict([])
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        IdentifierReference.from_dict({**payload, "unknown": True})


def test_frozen_and_summary():
    model = _model()
    with pytest.raises(FrozenInstanceError):
        model.identifier_value = "changed"
    assert "active" in model.summary()
