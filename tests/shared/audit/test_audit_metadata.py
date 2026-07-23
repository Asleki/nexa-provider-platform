"""Tests for shared.audit.audit_metadata."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from shared.audit.audit_actor import AuditActor
from shared.audit.audit_errors import AuditMetadataError, AuditValidationError
from shared.audit.audit_metadata import AuditMetadata
from shared.audit.audit_source import AuditSource


def make_actor() -> AuditActor:
    return AuditActor(actor_id="ACTOR-001", actor_type="employee")


def make_source() -> AuditSource:
    return AuditSource(source="provider-registry")


def test_metadata_normalizes_and_exposes_values() -> None:
    metadata = AuditMetadata(
        actor=make_actor(),
        source=make_source(),
        runtime_id="  RUN-001  ",
        runtime_mode="  simulation  ",
        correlation_id="  CORR-001  ",
        causation_id="  CAUSE-001  ",
        attributes={"tenant": "nexa"},
    )

    assert metadata.actor.actor_id == "ACTOR-001"
    assert metadata.source.source == "provider-registry"
    assert metadata.runtime_id == "RUN-001"
    assert metadata.runtime_mode == "simulation"
    assert metadata.correlation_id == "CORR-001"
    assert metadata.causation_id == "CAUSE-001"
    assert metadata.attributes == {"tenant": "nexa"}


@pytest.mark.parametrize("field_name", ["runtime_id", "runtime_mode"])
@pytest.mark.parametrize("value", ["", "   ", 123, None])
def test_required_runtime_text_validation(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "actor": make_actor(),
        "source": make_source(),
        "runtime_id": "RUN-001",
        "runtime_mode": "production",
    }
    values[field_name] = value

    with pytest.raises(AuditValidationError):
        AuditMetadata(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["correlation_id", "causation_id"])
@pytest.mark.parametrize("value", ["", "   ", 123])
def test_optional_trace_text_validation(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "actor": make_actor(),
        "source": make_source(),
        "runtime_id": "RUN-001",
        "runtime_mode": "production",
        field_name: value,
    }

    with pytest.raises(AuditValidationError):
        AuditMetadata(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [None, {}, "actor", object()])
def test_actor_must_be_audit_actor(value: object) -> None:
    with pytest.raises(AuditMetadataError, match="AuditActor"):
        AuditMetadata(
            actor=value,  # type: ignore[arg-type]
            source=make_source(),
            runtime_id="RUN-001",
            runtime_mode="production",
        )


@pytest.mark.parametrize("value", [None, {}, "source", object()])
def test_source_must_be_audit_source(value: object) -> None:
    with pytest.raises(AuditMetadataError, match="AuditSource"):
        AuditMetadata(
            actor=make_actor(),
            source=value,  # type: ignore[arg-type]
            runtime_id="RUN-001",
            runtime_mode="production",
        )


def test_attributes_are_defensively_copied_and_immutable() -> None:
    attributes = {"tenant": "nexa"}
    metadata = AuditMetadata(
        actor=make_actor(),
        source=make_source(),
        runtime_id="RUN-001",
        runtime_mode="production",
        attributes=attributes,
    )
    attributes["tenant"] = "changed"

    assert isinstance(metadata.attributes, MappingProxyType)
    assert metadata.attributes["tenant"] == "nexa"

    with pytest.raises(TypeError):
        metadata.attributes["tenant"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize("value", [None, "x", 123, [], object()])
def test_attributes_must_be_mapping(value: object) -> None:
    with pytest.raises(AuditMetadataError):
        AuditMetadata(
            actor=make_actor(),
            source=make_source(),
            runtime_id="RUN-001",
            runtime_mode="production",
            attributes=value,  # type: ignore[arg-type]
        )


def test_metadata_is_frozen() -> None:
    metadata = AuditMetadata(
        actor=make_actor(),
        source=make_source(),
        runtime_id="RUN-001",
        runtime_mode="production",
    )

    with pytest.raises(FrozenInstanceError):
        metadata.runtime_mode = "changed"  # type: ignore[misc]


def test_to_dict_returns_deeply_detached_dictionary() -> None:
    metadata = AuditMetadata(
        actor=AuditActor(
            actor_id="ACTOR-001",
            actor_type="service",
            attributes={"scope": "write"},
        ),
        source=AuditSource(
            source="npp",
            attributes={"transport": "api"},
        ),
        runtime_id="RUN-001",
        runtime_mode="production",
        attributes={"tenant": "nexa"},
    )

    data = metadata.to_dict()
    data["actor"]["attributes"]["scope"] = "changed"
    data["source"]["attributes"]["transport"] = "changed"
    data["attributes"]["tenant"] = "changed"

    assert metadata.actor.attributes["scope"] == "write"
    assert metadata.source.attributes["transport"] == "api"
    assert metadata.attributes["tenant"] == "nexa"
