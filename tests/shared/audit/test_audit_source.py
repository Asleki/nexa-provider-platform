"""Tests for shared.audit.audit_source."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from shared.audit.audit_errors import AuditMetadataError, AuditValidationError
from shared.audit.audit_source import AuditSource


def test_source_normalizes_and_exposes_values() -> None:
    source = AuditSource(
        source="  provider-registry  ",
        source_type="  service  ",
        source_id="  registry-001  ",
        request_id="  request-001  ",
        device_id="  device-001  ",
        event_id="  event-001  ",
        event_type="  provider.registered  ",
        attributes={"transport": "api"},
    )

    assert source.source == "provider-registry"
    assert source.source_type == "service"
    assert source.source_id == "registry-001"
    assert source.request_id == "request-001"
    assert source.device_id == "device-001"
    assert source.event_id == "event-001"
    assert source.event_type == "provider.registered"
    assert source.attributes == {"transport": "api"}


@pytest.mark.parametrize("value", ["", "   ", 123, None])
def test_source_is_required(value: object) -> None:
    with pytest.raises(AuditValidationError):
        AuditSource(source=value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "source_type",
        "source_id",
        "request_id",
        "device_id",
    ],
)
@pytest.mark.parametrize("value", ["", "   ", 123])
def test_optional_text_validation(field_name: str, value: object) -> None:
    values: dict[str, object] = {"source": "npp", field_name: value}

    with pytest.raises(AuditValidationError):
        AuditSource(**values)  # type: ignore[arg-type]


def test_event_id_and_event_type_must_be_provided_together() -> None:
    with pytest.raises(
        AuditValidationError,
        match="event_id and event_type must be provided together",
    ):
        AuditSource(source="npp", event_id="event-001")

    with pytest.raises(
        AuditValidationError,
        match="event_id and event_type must be provided together",
    ):
        AuditSource(source="npp", event_type="provider.registered")


def test_attributes_are_defensively_copied_and_immutable() -> None:
    attributes = {"transport": "cli"}
    source = AuditSource(source="npp", attributes=attributes)
    attributes["transport"] = "changed"

    assert isinstance(source.attributes, MappingProxyType)
    assert source.attributes["transport"] == "cli"

    with pytest.raises(TypeError):
        source.attributes["transport"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize("value", [None, "x", 123, [], object()])
def test_attributes_must_be_mapping(value: object) -> None:
    with pytest.raises(AuditMetadataError):
        AuditSource(source="npp", attributes=value)  # type: ignore[arg-type]


def test_source_is_frozen() -> None:
    source = AuditSource(source="npp")

    with pytest.raises(FrozenInstanceError):
        source.source = "changed"  # type: ignore[misc]


def test_to_dict_returns_detached_plain_dictionary() -> None:
    source = AuditSource(
        source="npp",
        source_type="service",
        attributes={"transport": "api"},
    )

    data = source.to_dict()
    data["attributes"]["transport"] = "changed"

    assert data["source"] == "npp"
    assert source.attributes["transport"] == "api"
