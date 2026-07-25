from dataclasses import FrozenInstanceError
from types import MappingProxyType
import pytest

from registries.core import NamespaceDefinition, NamespaceDefinitionError, RegistryStatus


def _model(**overrides):
    values = dict(namespace_id=" ns.civil ", registry_id=" reg.birth ",
                  namespace_code=" civil ", namespace_name=" Civil Namespace ",
                  status="active", description=" Civil identifiers. ",
                  version=1, metadata={" owner ": "state"})
    values.update(overrides)
    return NamespaceDefinition(**values)


def test_namespace_model_is_normalized_immutable_and_serializable():
    model = _model()
    assert model.namespace_id == "ns.civil"
    assert model.namespace_code == "CIVIL"
    assert model.status is RegistryStatus.ACTIVE
    assert model.identity == ("ns.civil", "CIVIL")
    assert model.registry_identity == ("reg.birth", "ns.civil")
    assert model.qualified_code == "reg.birth:CIVIL"
    assert isinstance(model.metadata, MappingProxyType)
    assert NamespaceDefinition.from_dict(model.to_dict()) == model
    with pytest.raises(FrozenInstanceError):
        model.namespace_name = "Changed"


@pytest.mark.parametrize("field", ["namespace_id", "registry_id", "namespace_code", "namespace_name"])
def test_namespace_required_fields(field):
    with pytest.raises(NamespaceDefinitionError):
        _model(**{field: " "})
    with pytest.raises(TypeError):
        _model(**{field: 1})


def test_namespace_strict_mapping_and_metadata_guards():
    with pytest.raises(TypeError, match="values must be a mapping"):
        NamespaceDefinition.from_dict([])
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        NamespaceDefinition.from_dict({**_model().to_dict(), "unknown": True})
    with pytest.raises(TypeError, match="metadata keys must be text"):
        _model(metadata={1: "x"})
    with pytest.raises(NamespaceDefinitionError, match="metadata keys cannot be empty"):
        _model(metadata={" ": "x"})
