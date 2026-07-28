import pytest

from registries.metadata import RegistryCapability, RegistryCapabilityError


def test_attributes_are_recursively_snapshotted_and_immutable():
    source = {"requirements": {"units": ["CELSIUS"]}}
    capability = RegistryCapability(
        "weather-observe-v1",
        "ENVIRONMENT.WEATHER.OBSERVE",
        "Observe Weather",
        "simulation",
        attributes=source,
    )

    source["requirements"]["units"].append("KELVIN")

    with pytest.raises(TypeError):
        capability.attributes["new"] = True
    with pytest.raises(TypeError):
        capability.attributes["requirements"]["new"] = True
    with pytest.raises(AttributeError):
        capability.attributes["requirements"]["units"].append("FAHRENHEIT")

    assert capability.to_dict()["attributes"] == {
        "requirements": {"units": ["CELSIUS"]}
    }


def test_attribute_keys_are_normalized_and_collisions_rejected():
    capability = RegistryCapability(
        "school-register-v1",
        "EDUCATION.SCHOOL.REGISTER",
        "Register School",
        "identity",
        attributes={" jurisdiction ": "NoveGeo"},
    )
    assert tuple(capability.attributes) == ("jurisdiction",)

    with pytest.raises(RegistryCapabilityError):
        RegistryCapability(
            "school-register-v1",
            "EDUCATION.SCHOOL.REGISTER",
            "Register School",
            "identity",
            attributes={"scope": "A", " scope ": "B"},
        )
