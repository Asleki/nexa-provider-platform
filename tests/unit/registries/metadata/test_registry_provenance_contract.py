from datetime import datetime, timezone

import pytest

from registries.metadata import (
    RegistryProvenance,
    RegistryProvenanceError,
    RegistryProvenanceSourceType,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)


def make(**overrides):
    values = {
        "source_type": "system",
        "source_system": "npp",
        "recorded_at": NOW,
    }
    values.update(overrides)
    return RegistryProvenance(**values)


def test_known_sources_require_a_source_system():
    with pytest.raises(RegistryProvenanceError, match="source_system cannot be empty"):
        make(source_system="")


def test_unknown_source_is_explicit_conservative_and_explained():
    item = make(
        source_type="unknown",
        source_system="",
        reason=" Legacy record did not retain origin metadata. ",
    )
    assert item.source_type is RegistryProvenanceSourceType.UNKNOWN
    assert item.reason == "Legacy record did not retain origin metadata."
    assert item.verified is False


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"source_type": "unknown", "source_system": "legacy"}, "cannot claim"),
        ({"source_type": "unknown", "source_system": "", "reason": ""}, "requires a reason"),
        ({"source_type": "unknown", "source_system": "", "reason": "missing", "verified": True, "verification_reference": "V-1"}, "cannot be marked verified"),
    ],
)
def test_unknown_source_rejects_false_certainty(overrides, message):
    with pytest.raises(RegistryProvenanceError, match=message):
        make(**overrides)


def test_simulation_generator_and_generated_flag_are_bidirectionally_consistent():
    item = make(
        source_type="simulation_generator",
        source_system="nexilabs",
        generated=True,
        generator_name="population-generator",
    )
    assert item.generated is True

    with pytest.raises(RegistryProvenanceError, match="requires generated=True"):
        make(source_type="simulation_generator", source_system="nexilabs")
    with pytest.raises(RegistryProvenanceError, match="requires source_type"):
        make(generated=True, generator_name="generator")


def test_non_generated_provenance_rejects_generator_details():
    with pytest.raises(RegistryProvenanceError, match="cannot contain generator details"):
        make(generator_name="not-applicable")


def test_generator_version_requires_generator_name():
    with pytest.raises(RegistryProvenanceError, match="requires generator_name"):
        make(
            source_type="simulation_generator",
            source_system="nexilabs",
            generated=True,
            generator_version="2",
            generation_batch_id="BATCH-1",
        )


@pytest.mark.parametrize("source_type", ["import", "derived"])
def test_import_and_derived_sources_require_trace_information(source_type):
    with pytest.raises(RegistryProvenanceError, match="requires a source reference"):
        make(source_type=source_type)

    assert make(source_type=source_type, source_reference="UPSTREAM-1").source_reference == "UPSTREAM-1"
    assert make(source_type=source_type, reason="Historical source summary").reason


def test_actor_institution_and_event_identifiers_can_coexist():
    item = make(
        source_type="institution",
        source_system="hospital-registry",
        source_actor_id="DOCTOR-1",
        source_institution_id="HOSPITAL-1",
        source_event_id="BIRTH-REGISTERED-1",
    )
    assert (item.source_actor_id, item.source_institution_id, item.source_event_id) == (
        "DOCTOR-1",
        "HOSPITAL-1",
        "BIRTH-REGISTERED-1",
    )


def test_text_fields_are_trimmed_and_bounded():
    item = make(source_system=" npp ", source_reference=" SRC-1 ", reason=" note ")
    assert item.source_system == "npp"
    assert item.source_reference == "SRC-1"
    assert item.reason == "note"

    with pytest.raises(RegistryProvenanceError, match="reason cannot exceed"):
        make(reason="x" * 2001)
    with pytest.raises(RegistryProvenanceError, match="source_system cannot exceed"):
        make(source_system="x" * 256)


def test_invalid_source_type_is_exposed_as_provenance_domain_error():
    with pytest.raises(RegistryProvenanceError, match="Unsupported provenance source type"):
        make(source_type="device")


def test_wrong_source_type_python_type_remains_type_error():
    with pytest.raises(TypeError, match="source type must be text"):
        make(source_type=7)


@pytest.mark.parametrize("version", [0, -1])
def test_version_must_be_positive(version):
    with pytest.raises(RegistryProvenanceError, match="at least 1"):
        make(version=version)


@pytest.mark.parametrize("version", [True, 1.5, "1"])
def test_version_requires_a_real_integer(version):
    with pytest.raises(TypeError, match="version must be an integer"):
        make(version=version)
