from dataclasses import replace

import pytest

from registries.relationships import (
    RegistryReference,
    RelationshipDefinition,
    RelationshipType,
)
from registries.relationships.immutable_reference_result import (
    ImmutableReferenceField,
    ImmutableReferenceViolationCode,
)
from registries.relationships.immutable_reference_rules import (
    ImmutableReferenceViolation,
    assert_registry_reference_unchanged,
    assert_relationship_definition_unchanged,
    compare_registry_references,
    compare_relationship_definitions,
    registry_reference_identity_key,
    relationship_identity_key,
)


def relationship(**changes):
    value = RelationshipDefinition(
        relationship_id="rel-001",
        relationship_type=RelationshipType(
            "type.school.enrolment",
            "EDUCATION.ENROLLED_AT",
            "Enrolled At",
            description="Current school enrolment.",
            attributes={"display_group": "education"},
        ),
        source=RegistryReference(
            "citizen.registry", "citizen-001", attributes={"hint": "student"}
        ),
        target=RegistryReference(
            "school.registry", "school-001", attributes={"hint": "school"}
        ),
        runtime_mode="simulation",
        attributes={"status": "active"},
    )
    return replace(value, **changes) if changes else value


def test_registry_reference_identity_key_is_registry_record_and_version():
    reference = RegistryReference("citizen.registry", "000001", 2, {"name": "masked"})
    assert registry_reference_identity_key(reference) == (
        "citizen.registry",
        "000001",
        2,
    )


def test_registry_reference_attributes_do_not_change_identity():
    existing = RegistryReference("citizen.registry", "000001", attributes={"a": 1})
    proposed = RegistryReference("citizen.registry", "000001", attributes={"a": 2})
    result = compare_registry_references(existing, proposed)
    assert result.is_compatible is True
    assert registry_reference_identity_key(existing) == registry_reference_identity_key(proposed)


@pytest.mark.parametrize(
    ("proposed", "field", "code"),
    [
        (
            RegistryReference("student.registry", "000001"),
            ImmutableReferenceField.REGISTRY_ID,
            ImmutableReferenceViolationCode.REGISTRY_ID_CHANGED,
        ),
        (
            RegistryReference("citizen.registry", "000002"),
            ImmutableReferenceField.RECORD_ID,
            ImmutableReferenceViolationCode.RECORD_ID_CHANGED,
        ),
        (
            RegistryReference("citizen.registry", "000001", 2),
            ImmutableReferenceField.REFERENCE_VERSION,
            ImmutableReferenceViolationCode.REFERENCE_VERSION_CHANGED,
        ),
    ],
)
def test_registry_reference_changes_are_reported(proposed, field, code):
    existing = RegistryReference("citizen.registry", "000001")
    result = compare_registry_references(existing, proposed)
    assert result.is_compatible is False
    assert result.changed_fields == (field,)
    assert result.violations == (code,)


def test_same_record_id_in_different_registries_is_not_compatible():
    result = compare_registry_references(
        RegistryReference("citizen.registry", "000001"),
        RegistryReference("school.registry", "000001"),
    )
    assert result.changed_fields == (ImmutableReferenceField.REGISTRY_ID,)


def test_registry_reference_assertion_raises_structured_violation():
    existing = RegistryReference("citizen.registry", "000001")
    proposed = RegistryReference("citizen.registry", "000002")
    with pytest.raises(ImmutableReferenceViolation) as captured:
        assert_registry_reference_unchanged(existing, proposed)
    assert captured.value.result == compare_registry_references(existing, proposed)
    assert "record_id" in str(captured.value)


def test_registry_reference_assertion_returns_none_when_compatible():
    existing = RegistryReference("citizen.registry", "000001")
    assert assert_registry_reference_unchanged(existing, existing) is None


def test_relationship_identity_key_excludes_descriptive_attributes():
    existing = relationship()
    proposed = replace(
        existing,
        relationship_type=replace(
            existing.relationship_type,
            relationship_type_name="School Enrolment",
            description="Renamed for display.",
            attributes={"display_group": "learning"},
        ),
        source=replace(existing.source, attributes={"hint": "learner"}),
        target=replace(existing.target, attributes={"hint": "institution"}),
        attributes={"status": "historical"},
    )
    assert relationship_identity_key(existing) == relationship_identity_key(proposed)
    assert compare_relationship_definitions(existing, proposed).is_compatible is True


@pytest.mark.parametrize(
    ("changes", "field", "code"),
    [
        (
            {"relationship_id": "rel-002"},
            ImmutableReferenceField.RELATIONSHIP_ID,
            ImmutableReferenceViolationCode.RELATIONSHIP_ID_CHANGED,
        ),
        (
            {
                "relationship_type": RelationshipType(
                    "type.school.transfer", "EDUCATION.ENROLLED_AT", "Transferred Type"
                )
            },
            ImmutableReferenceField.RELATIONSHIP_TYPE_ID,
            ImmutableReferenceViolationCode.RELATIONSHIP_TYPE_ID_CHANGED,
        ),
        (
            {
                "relationship_type": RelationshipType(
                    "type.school.enrolment", "EDUCATION.ATTENDS", "Attends"
                )
            },
            ImmutableReferenceField.RELATIONSHIP_TYPE_CODE,
            ImmutableReferenceViolationCode.RELATIONSHIP_TYPE_CODE_CHANGED,
        ),
        (
            {"source": RegistryReference("person.registry", "citizen-001")},
            ImmutableReferenceField.SOURCE_REGISTRY_ID,
            ImmutableReferenceViolationCode.SOURCE_REGISTRY_ID_CHANGED,
        ),
        (
            {"source": RegistryReference("citizen.registry", "citizen-002")},
            ImmutableReferenceField.SOURCE_RECORD_ID,
            ImmutableReferenceViolationCode.SOURCE_RECORD_ID_CHANGED,
        ),
        (
            {"source": RegistryReference("citizen.registry", "citizen-001", 2)},
            ImmutableReferenceField.SOURCE_VERSION,
            ImmutableReferenceViolationCode.SOURCE_VERSION_CHANGED,
        ),
        (
            {"target": RegistryReference("institution.registry", "school-001")},
            ImmutableReferenceField.TARGET_REGISTRY_ID,
            ImmutableReferenceViolationCode.TARGET_REGISTRY_ID_CHANGED,
        ),
        (
            {"target": RegistryReference("school.registry", "school-002")},
            ImmutableReferenceField.TARGET_RECORD_ID,
            ImmutableReferenceViolationCode.TARGET_RECORD_ID_CHANGED,
        ),
        (
            {"target": RegistryReference("school.registry", "school-001", 2)},
            ImmutableReferenceField.TARGET_VERSION,
            ImmutableReferenceViolationCode.TARGET_VERSION_CHANGED,
        ),
        (
            {"runtime_mode": "production"},
            ImmutableReferenceField.RUNTIME_MODE,
            ImmutableReferenceViolationCode.RUNTIME_MODE_CHANGED,
        ),
        (
            {"version": 2},
            ImmutableReferenceField.RELATIONSHIP_VERSION,
            ImmutableReferenceViolationCode.RELATIONSHIP_VERSION_CHANGED,
        ),
    ],
)
def test_each_relationship_identity_change_is_reported(changes, field, code):
    existing = relationship()
    result = compare_relationship_definitions(existing, relationship(**changes))
    assert result.is_compatible is False
    assert result.changed_fields == (field,)
    assert result.violations == (code,)


def test_relationship_comparison_reports_all_changes_in_stable_order():
    existing = relationship()
    proposed = relationship(
        relationship_id="rel-002",
        source=RegistryReference("person.registry", "citizen-002", 2),
        target=RegistryReference("institution.registry", "school-002", 2),
        runtime_mode="production",
        version=2,
    )
    result = compare_relationship_definitions(existing, proposed)
    assert result.changed_fields == (
        ImmutableReferenceField.RELATIONSHIP_ID,
        ImmutableReferenceField.SOURCE_REGISTRY_ID,
        ImmutableReferenceField.SOURCE_RECORD_ID,
        ImmutableReferenceField.SOURCE_VERSION,
        ImmutableReferenceField.TARGET_REGISTRY_ID,
        ImmutableReferenceField.TARGET_RECORD_ID,
        ImmutableReferenceField.TARGET_VERSION,
        ImmutableReferenceField.RUNTIME_MODE,
        ImmutableReferenceField.RELATIONSHIP_VERSION,
    )


def test_runtime_mode_normalisation_preserves_compatible_identity():
    existing = relationship(runtime_mode="simulation")
    proposed = relationship(runtime_mode=" SIMULATION ")
    assert compare_relationship_definitions(existing, proposed).is_compatible is True


def test_relationship_assertion_raises_with_structured_result():
    existing = relationship()
    proposed = relationship(runtime_mode="production")
    with pytest.raises(ImmutableReferenceViolation) as captured:
        assert_relationship_definition_unchanged(existing, proposed)
    assert captured.value.result.changed_fields == (
        ImmutableReferenceField.RUNTIME_MODE,
    )


def test_relationship_assertion_returns_none_when_identity_is_unchanged():
    existing = relationship()
    proposed = replace(existing, attributes={"status": "ended"})
    assert assert_relationship_definition_unchanged(existing, proposed) is None


@pytest.mark.parametrize(
    ("function", "args"),
    [
        (registry_reference_identity_key, (object(),)),
        (relationship_identity_key, (object(),)),
        (compare_registry_references, (object(), RegistryReference("a.registry", "1"))),
        (compare_registry_references, (RegistryReference("a.registry", "1"), object())),
        (compare_relationship_definitions, (object(), relationship())),
        (compare_relationship_definitions, (relationship(), object())),
    ],
)
def test_rules_reject_wrong_contract_types(function, args):
    with pytest.raises(TypeError):
        function(*args)
