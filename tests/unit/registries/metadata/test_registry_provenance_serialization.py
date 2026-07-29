from datetime import datetime, timezone

import pytest

from registries.metadata import RegistryProvenance

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)


def build():
    return RegistryProvenance(
        source_type="simulation_generator",
        source_system="nexilabs",
        source_reference="CITIZEN-1",
        source_event_id="CITIZEN-GENERATED-1",
        generated=True,
        generator_name="population-generator",
        generator_version="1.0",
        generation_batch_id="NVG-POP-1",
        generation_seed_reference="NVG-FOUNDATION-0001",
        recorded_at=NOW,
        verified=True,
        verification_reference="VERIFY-1",
        attributes={"rules": {"domains": ["identity", "education"], "versions": {2, 1}}},
        reason="Initial deterministic population generation.",
    )


def test_to_dict_has_complete_stable_shape_and_detached_values():
    data = build().to_dict()
    assert tuple(data) == (
        "source_type",
        "source_system",
        "source_reference",
        "source_actor_id",
        "source_institution_id",
        "source_event_id",
        "generated",
        "generator_name",
        "generator_version",
        "generation_batch_id",
        "generation_seed_reference",
        "recorded_at",
        "verified",
        "verified_at",
        "verification_reference",
        "version",
        "attributes",
        "reason",
    )
    assert data["source_type"] == "simulation_generator"
    assert data["recorded_at"] == "2026-07-29T12:00:00+00:00"
    assert data["attributes"]["rules"]["versions"] == [1, 2]


def test_round_trip_preserves_the_contract():
    original = build()
    rebuilt = RegistryProvenance.from_dict(original.to_dict())
    assert rebuilt.to_dict() == original.to_dict()


def test_serialized_output_is_detached_from_the_contract():
    item = build()
    output = item.to_dict()
    output["attributes"]["rules"]["domains"].append("health")
    assert item.to_dict()["attributes"]["rules"]["domains"] == ["identity", "education"]


def test_from_dict_does_not_retain_the_callers_mapping():
    payload = build().to_dict()
    item = RegistryProvenance.from_dict(payload)
    payload["attributes"]["rules"]["domains"].append("finance")
    assert "finance" not in item.to_dict()["attributes"]["rules"]["domains"]


def test_from_dict_requires_a_mapping():
    with pytest.raises(TypeError, match="data must be a mapping"):
        RegistryProvenance.from_dict([])
