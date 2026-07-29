from registries.relationships import RegistryReference, RelationshipDefinition, RelationshipType


def test_relationship_identity_is_not_endpoint_or_type_identity():
    relationship_type = RelationshipType("type.employment", "EMPLOYMENT.WORKS_FOR", "Works For")
    relationship = RelationshipDefinition(
        "rel-100",
        relationship_type,
        RegistryReference("citizen.registry", "NVG-CIT-1"),
        RegistryReference("business.registry", "NVG-BUS-1"),
        "simulation",
    )
    assert relationship.relationship_id not in {
        relationship.relationship_type.relationship_type_id,
        relationship.source.record_id,
        relationship.target.record_id,
    }


def test_same_endpoints_can_carry_distinct_semantic_relationships():
    source = RegistryReference("citizen.registry", "NVG-CIT-1")
    target = RegistryReference("business.registry", "NVG-BUS-1")
    employee = RelationshipDefinition(
        "rel-employee",
        RelationshipType("type.employed_by", "EMPLOYMENT.EMPLOYED_BY", "Employed By"),
        source,
        target,
        "simulation",
    )
    owner = RelationshipDefinition(
        "rel-owner",
        RelationshipType("type.owns", "BUSINESS.OWNS", "Owns"),
        source,
        target,
        "simulation",
    )
    assert employee.source == owner.source
    assert employee.target == owner.target
    assert employee.relationship_type != owner.relationship_type
