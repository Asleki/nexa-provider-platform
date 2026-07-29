from dataclasses import FrozenInstanceError

import pytest

from registries.relationships.direction_contract import (
    RelationshipDirection,
    RelationshipDirectionError,
    RelationshipDirectionMode,
)
from registries.relationships.relationship_type import RelationshipType


def _type(type_id="employment.employs", code="EMPLOYMENT.EMPLOYS", version=1):
    return RelationshipType(type_id, code, "Employs", version=version)


def _inverse_type():
    return RelationshipType(
        "employment.employed_by", "EMPLOYMENT.EMPLOYED_BY", "Employed by"
    )


def _direction(mode=RelationshipDirectionMode.INVERSE, **changes):
    values = {
        "direction_id": "direction.employment",
        "direction_code": "DIRECTION.EMPLOYMENT",
        "mode": mode,
        "forward_type": _type(),
        "inverse_type": _inverse_type() if mode is RelationshipDirectionMode.INVERSE else None,
        "forward_label": "employs",
        "reverse_label": "employed by" if mode is not RelationshipDirectionMode.FORWARD_ONLY else "",
        "version": 1,
    }
    values.update(changes)
    return RelationshipDirection(**values)


def test_inverse_direction_exposes_explicit_reverse_type():
    direction = _direction()
    assert direction.allows_reverse is True
    assert direction.preserves_meaning_when_reversed is False
    assert direction.type_for_reverse() == _inverse_type()


def test_forward_only_direction_has_no_reverse_type():
    direction = _direction(RelationshipDirectionMode.FORWARD_ONLY)
    assert direction.allows_reverse is False
    assert direction.type_for_reverse() is None


def test_symmetric_direction_reuses_forward_type():
    direction = _direction(
        RelationshipDirectionMode.SYMMETRIC,
        forward_type=RelationshipType("family.married", "FAMILY.MARRIED_TO", "Married to"),
    )
    assert direction.allows_reverse is True
    assert direction.preserves_meaning_when_reversed is True
    assert direction.inverse_type is direction.forward_type


def test_symmetric_direction_accepts_equivalent_repeated_type():
    relationship_type = RelationshipType("family.married", "FAMILY.MARRIED_TO", "Married")
    direction = _direction(
        RelationshipDirectionMode.SYMMETRIC,
        forward_type=relationship_type,
        inverse_type=RelationshipType("family.married", "FAMILY.MARRIED_TO", "Spouse"),
    )
    assert direction.inverse_type is relationship_type


@pytest.mark.parametrize("field", ["direction_id", "direction_code"])
def test_required_identity_fields_reject_empty_text(field):
    with pytest.raises(RelationshipDirectionError):
        _direction(**{field: "  "})


def test_direction_code_is_normalised_to_uppercase():
    assert _direction(direction_code="direction.employment").direction_code == "DIRECTION.EMPLOYMENT"


@pytest.mark.parametrize(
    "changes",
    [
        {"direction_id": "bad value"},
        {"direction_code": "SINGLE"},
        {"direction_code": "DIRECTION.bad-code"},
        {"version": 0},
        {"version": -1},
    ],
)
def test_invalid_structure_is_rejected(changes):
    with pytest.raises(RelationshipDirectionError):
        _direction(**changes)


def test_boolean_version_is_rejected():
    with pytest.raises(TypeError):
        _direction(version=True)


def test_forward_only_rejects_inverse_type():
    with pytest.raises(RelationshipDirectionError):
        _direction(RelationshipDirectionMode.FORWARD_ONLY, inverse_type=_inverse_type())


def test_forward_only_rejects_reverse_label():
    with pytest.raises(RelationshipDirectionError):
        _direction(RelationshipDirectionMode.FORWARD_ONLY, reverse_label="reverse")


def test_inverse_mode_requires_inverse_type():
    with pytest.raises(RelationshipDirectionError):
        _direction(inverse_type=None)


def test_inverse_mode_rejects_same_semantic_type():
    with pytest.raises(RelationshipDirectionError):
        _direction(inverse_type=_type())


def test_symmetric_mode_rejects_distinct_inverse_type():
    with pytest.raises(RelationshipDirectionError):
        _direction(RelationshipDirectionMode.SYMMETRIC, inverse_type=_inverse_type())


def test_direction_is_frozen():
    direction = _direction()
    with pytest.raises(FrozenInstanceError):
        direction.version = 2


def test_serialization_round_trip_is_deterministic():
    direction = _direction()
    payload = direction.to_dict()
    assert RelationshipDirection.from_dict(payload) == direction
    assert RelationshipDirection.from_dict(payload).to_dict() == payload


def test_serialization_returns_detached_nested_data():
    payload = _direction().to_dict()
    payload["forward_type"]["relationship_type_name"] = "Changed"
    assert _direction().forward_type.relationship_type_name == "Employs"


def test_from_dict_rejects_unknown_fields():
    payload = _direction().to_dict()
    payload["unexpected"] = True
    with pytest.raises(RelationshipDirectionError):
        RelationshipDirection.from_dict(payload)


def test_from_dict_rejects_unknown_mode():
    payload = _direction().to_dict()
    payload["mode"] = "bidirectional"
    with pytest.raises(RelationshipDirectionError):
        RelationshipDirection.from_dict(payload)


def test_label_length_is_bounded():
    with pytest.raises(RelationshipDirectionError):
        _direction(forward_label="x" * 201)


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode", "inverse"),
        ("forward_type", object()),
        ("inverse_type", object()),
        ("forward_label", 1),
        ("reverse_label", 1),
    ],
)
def test_wrong_field_types_are_rejected(field, value):
    with pytest.raises(TypeError):
        _direction(**{field: value})
