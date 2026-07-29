import pytest

from registries.relationships import RelationshipType, RelationshipTypeError


def make_type(**overrides):
    values = {
        "relationship_type_id": "relationship.education.enrolled_at",
        "relationship_type_code": "education.enrolled_at",
        "relationship_type_name": "Enrolled At",
    }
    values.update(overrides)
    return RelationshipType(**values)


def test_relationship_type_normalises_semantic_fields():
    value = make_type(
        relationship_type_id=" relationship.education.enrolled_at ",
        relationship_type_code=" education.enrolled_at ",
        relationship_type_name=" Enrolled At ",
        description=" Student enrolment link. ",
    )
    assert value.relationship_type_id == "relationship.education.enrolled_at"
    assert value.relationship_type_code == "EDUCATION.ENROLLED_AT"
    assert value.relationship_type_name == "Enrolled At"
    assert value.description == "Student enrolment link."


def test_relationship_type_is_extensible_beyond_bootstrap_types():
    values = [
        make_type(),
        make_type(
            relationship_type_id="relationship.health.treated_at",
            relationship_type_code="HEALTH.TREATED_AT",
            relationship_type_name="Treated At",
        ),
        make_type(
            relationship_type_id="relationship.telecom.sim_registered_to",
            relationship_type_code="TELECOM.SIM_REGISTERED_TO",
            relationship_type_name="SIM Registered To",
        ),
    ]
    assert len({item.relationship_type_id for item in values}) == 3


def test_relationship_type_rejects_flat_code():
    with pytest.raises(RelationshipTypeError, match="hierarchical dotted code"):
        make_type(relationship_type_code="ENROLLED_AT")


def test_relationship_type_identity_is_independent_of_display_name():
    first = make_type(relationship_type_name="Enrolled At")
    renamed = make_type(relationship_type_name="Student of School")
    assert first.relationship_type_id == renamed.relationship_type_id
    assert first.relationship_type_name != renamed.relationship_type_name


def test_relationship_type_rejects_invalid_version():
    with pytest.raises(RelationshipTypeError, match="at least 1"):
        make_type(version=0)
