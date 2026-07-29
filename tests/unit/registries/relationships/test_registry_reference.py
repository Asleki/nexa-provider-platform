from dataclasses import FrozenInstanceError

import pytest

from registries.relationships import RegistryReference, RegistryReferenceError


def test_registry_reference_normalises_identity_and_version():
    ref = RegistryReference(" citizen.registry ", " NVG-CIT-000001 ", version=2)
    assert ref.registry_id == "citizen.registry"
    assert ref.record_id == "NVG-CIT-000001"
    assert ref.version == 2


@pytest.mark.parametrize("field", ["registry_id", "record_id"])
def test_registry_reference_rejects_non_text_identity(field):
    kwargs = {"registry_id": "citizen.registry", "record_id": "NVG-CIT-1"}
    kwargs[field] = 1
    with pytest.raises(TypeError, match=f"{field} must be text"):
        RegistryReference(**kwargs)


@pytest.mark.parametrize("field", ["registry_id", "record_id"])
def test_registry_reference_rejects_empty_identity(field):
    kwargs = {"registry_id": "citizen.registry", "record_id": "NVG-CIT-1"}
    kwargs[field] = "   "
    with pytest.raises(RegistryReferenceError, match=f"{field} cannot be empty"):
        RegistryReference(**kwargs)


def test_registry_reference_rejects_invalid_characters():
    with pytest.raises(RegistryReferenceError, match="registry_id must start"):
        RegistryReference("citizen registry", "NVG-CIT-1")
    with pytest.raises(RegistryReferenceError, match="record_id must start"):
        RegistryReference("citizen.registry", "NVG CIT 1")


@pytest.mark.parametrize("value", [True, 1.5, "1"])
def test_registry_reference_rejects_non_integer_versions(value):
    with pytest.raises(TypeError, match="version must be an integer"):
        RegistryReference("citizen.registry", "NVG-CIT-1", version=value)


def test_registry_reference_rejects_non_positive_version():
    with pytest.raises(RegistryReferenceError, match="at least 1"):
        RegistryReference("citizen.registry", "NVG-CIT-1", version=0)


def test_registry_reference_is_frozen():
    ref = RegistryReference("citizen.registry", "NVG-CIT-1")
    with pytest.raises(FrozenInstanceError):
        ref.record_id = "NVG-CIT-2"


def test_same_record_id_can_exist_in_different_registries():
    person = RegistryReference("citizen.registry", "000001")
    school = RegistryReference("school.registry", "000001")
    assert person != school
