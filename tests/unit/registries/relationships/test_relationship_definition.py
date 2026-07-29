import pytest

from registries.relationships import (
    RegistryReference,
    RelationshipDefinition,
    RelationshipDefinitionError,
    RelationshipType,
)


def relationship_type():
    return RelationshipType(
        "relationship.education.enrolled_at",
        "EDUCATION.ENROLLED_AT",
        "Enrolled At",
    )


def reference(registry_id="citizen.registry", record_id="NVG-CIT-1"):
    return RegistryReference(registry_id, record_id)


def make_definition(**overrides):
    values = {
        "relationship_id": "rel-NVG-000001",
        "relationship_type": relationship_type(),
        "source": reference(),
        "target": reference("school.registry", "NVG-SCH-1"),
        "runtime_mode": "simulation",
    }
    values.update(overrides)
    return RelationshipDefinition(**values)


def test_relationship_definition_preserves_ordered_endpoints():
    value = make_definition()
    assert value.source.registry_id == "citizen.registry"
    assert value.target.registry_id == "school.registry"


def test_relationship_definition_normalises_identity_and_runtime_mode():
    value = make_definition(
        relationship_id=" rel-NVG-000001 ", runtime_mode=" SIMULATION "
    )
    assert value.relationship_id == "rel-NVG-000001"
    assert value.runtime_mode == "simulation"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("relationship_type", object(), "must be a RelationshipType"),
        ("source", object(), "must be a RegistryReference"),
        ("target", object(), "must be a RegistryReference"),
    ],
)
def test_relationship_definition_rejects_wrong_component_types(field, value, message):
    with pytest.raises(TypeError, match=message):
        make_definition(**{field: value})


def test_relationship_definition_rejects_invalid_runtime_mode():
    with pytest.raises(RelationshipDefinitionError, match="runtime_mode must start"):
        make_definition(runtime_mode="simulation mode")


def test_relationship_definition_does_not_forbid_self_reference_yet():
    ref = reference()
    value = make_definition(source=ref, target=ref)
    assert value.source == value.target


def test_relationship_definition_does_not_resolve_endpoints():
    value = make_definition()
    assert not hasattr(value, "resolve_source")
    assert not hasattr(value, "resolve_target")
