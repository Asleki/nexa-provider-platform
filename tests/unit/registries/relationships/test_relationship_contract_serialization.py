from registries.relationships import (
    RegistryReference,
    RelationshipDefinition,
    RelationshipType,
)


def make_definition():
    return RelationshipDefinition(
        relationship_id="rel-NVG-000001",
        relationship_type=RelationshipType(
            "relationship.business.owned_by",
            "BUSINESS.OWNED_BY",
            "Owned By",
            attributes={"labels": ["ownership"]},
        ),
        source=RegistryReference(
            "business.registry", "NVG-BUS-1", attributes={"scope": ["legal"]}
        ),
        target=RegistryReference("citizen.registry", "NVG-CIT-1"),
        runtime_mode="simulation",
        attributes={"notes": {"source": "incorporation"}},
    )


def test_complete_relationship_round_trip_is_canonical():
    original = make_definition()
    restored = RelationshipDefinition.from_dict(original.to_dict())
    assert restored == original
    assert restored.to_dict() == original.to_dict()


def test_serialized_output_is_detached_from_contract():
    value = make_definition()
    payload = value.to_dict()
    payload["attributes"]["notes"]["source"] = "changed"
    payload["source"]["attributes"]["scope"].append("changed")
    payload["relationship_type"]["attributes"]["labels"].append("changed")
    assert value.attributes["notes"]["source"] == "incorporation"
    assert value.source.attributes["scope"] == ("legal",)
    assert value.relationship_type.attributes["labels"] == ("ownership",)


def test_from_dict_accepts_existing_nested_contract_objects():
    value = make_definition()
    restored = RelationshipDefinition.from_dict(
        {
            "relationship_id": value.relationship_id,
            "relationship_type": value.relationship_type,
            "source": value.source,
            "target": value.target,
            "runtime_mode": value.runtime_mode,
        }
    )
    assert restored.relationship_type is value.relationship_type
    assert restored.source is value.source
