"""Tests for shared.audit.audit_actor."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from shared.audit.audit_actor import AuditActor
from shared.audit.audit_errors import AuditMetadataError, AuditValidationError


def test_actor_normalizes_and_exposes_values() -> None:
    actor = AuditActor(
        actor_id="  ACTOR-001  ",
        actor_type="  employee  ",
        actor_role="  registrar  ",
        actor_namespace="  identity  ",
        attributes={"channel": "cli"},
    )

    assert actor.actor_id == "ACTOR-001"
    assert actor.actor_type == "employee"
    assert actor.actor_role == "registrar"
    assert actor.actor_namespace == "identity"
    assert actor.attributes == {"channel": "cli"}


@pytest.mark.parametrize("field_name", ["actor_id", "actor_type"])
@pytest.mark.parametrize("value", ["", "   ", 123, None])
def test_required_text_validation(field_name: str, value: object) -> None:
    values = {"actor_id": "ACTOR-001", "actor_type": "employee"}
    values[field_name] = value

    with pytest.raises(AuditValidationError):
        AuditActor(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["actor_role", "actor_namespace"])
@pytest.mark.parametrize("value", ["", "   ", 123])
def test_optional_text_validation(field_name: str, value: object) -> None:
    values: dict[str, object] = {
        "actor_id": "ACTOR-001",
        "actor_type": "employee",
        field_name: value,
    }

    with pytest.raises(AuditValidationError):
        AuditActor(**values)  # type: ignore[arg-type]


def test_optional_values_default_to_none() -> None:
    actor = AuditActor(actor_id="ACTOR-001", actor_type="system")

    assert actor.actor_role is None
    assert actor.actor_namespace is None


def test_attributes_are_defensively_copied_and_immutable() -> None:
    attributes = {"channel": "api"}
    actor = AuditActor(
        actor_id="ACTOR-001",
        actor_type="service",
        attributes=attributes,
    )
    attributes["channel"] = "changed"

    assert isinstance(actor.attributes, MappingProxyType)
    assert actor.attributes["channel"] == "api"

    with pytest.raises(TypeError):
        actor.attributes["channel"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize("value", [None, "x", 123, [], object()])
def test_attributes_must_be_mapping(value: object) -> None:
    with pytest.raises(AuditMetadataError):
        AuditActor(
            actor_id="ACTOR-001",
            actor_type="service",
            attributes=value,  # type: ignore[arg-type]
        )


def test_actor_is_frozen() -> None:
    actor = AuditActor(actor_id="ACTOR-001", actor_type="service")

    with pytest.raises(FrozenInstanceError):
        actor.actor_type = "changed"  # type: ignore[misc]


def test_to_dict_returns_detached_plain_dictionary() -> None:
    actor = AuditActor(
        actor_id="ACTOR-001",
        actor_type="service",
        actor_role="writer",
        actor_namespace="registry",
        attributes={"scope": "citizen"},
    )

    data = actor.to_dict()
    data["attributes"]["scope"] = "changed"

    assert data["actor_id"] == "ACTOR-001"
    assert actor.attributes["scope"] == "citizen"
