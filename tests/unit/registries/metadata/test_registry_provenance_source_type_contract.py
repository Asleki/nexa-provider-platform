import pytest

from registries.metadata import RegistryProvenanceSourceType


def test_source_type_persisted_values_are_stable_and_complete():
    assert {item.name: item.value for item in RegistryProvenanceSourceType} == {
        "HUMAN": "human",
        "INSTITUTION": "institution",
        "SYSTEM": "system",
        "IMPORT": "import",
        "SIMULATION_GENERATOR": "simulation_generator",
        "DERIVED": "derived",
        "UNKNOWN": "unknown",
    }


def test_source_type_conversion_normalises_text_and_preserves_members():
    assert RegistryProvenanceSourceType.from_value("  HUMAN ") is RegistryProvenanceSourceType.HUMAN
    assert RegistryProvenanceSourceType.from_value(RegistryProvenanceSourceType.SYSTEM) is RegistryProvenanceSourceType.SYSTEM
    assert str(RegistryProvenanceSourceType.UNKNOWN) == "unknown"


@pytest.mark.parametrize("value", ["", "   "])
def test_source_type_rejects_empty_text(value):
    with pytest.raises(ValueError, match="cannot be empty"):
        RegistryProvenanceSourceType.from_value(value)


def test_source_type_rejects_unsupported_text():
    with pytest.raises(ValueError, match="Unsupported provenance source type"):
        RegistryProvenanceSourceType.from_value("device")


@pytest.mark.parametrize("value", [None, 7, object()])
def test_source_type_rejects_non_text_values(value):
    with pytest.raises(TypeError, match="must be text"):
        RegistryProvenanceSourceType.from_value(value)
