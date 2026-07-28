from registries.metadata import RegistryCapability


def test_serialization_returns_detached_nested_data_and_round_trips():
    source = {"requirements": {"units": ["CELSIUS", "KELVIN"]}}
    capability = RegistryCapability(
        "weather-observe-v1",
        "ENVIRONMENT.WEATHER.OBSERVE",
        "Observe Weather",
        "simulation",
        attributes=source,
    )

    source["requirements"]["units"].append("FAHRENHEIT")
    serialized = capability.to_dict()
    serialized["attributes"]["requirements"]["units"].append("RANKINE")

    assert capability.to_dict()["attributes"] == {
        "requirements": {"units": ["CELSIUS", "KELVIN"]}
    }
    assert RegistryCapability.from_dict(capability.to_dict()) == capability


def test_serialization_preserves_many_semantic_identifier_references_as_attributes():
    capability = RegistryCapability(
        "birth-certificate-issue-v1",
        "CIVIL.BIRTH.CERTIFICATE.ISSUE",
        "Issue Birth Certificate",
        "issuance",
        attributes={
            "reference_roles": [
                "event_id",
                "actor_id",
                "device_id",
                "citizen_id",
                "hospital_visitor_id",
            ]
        },
    )

    assert capability.to_dict()["attributes"]["reference_roles"] == [
        "event_id",
        "actor_id",
        "device_id",
        "citizen_id",
        "hospital_visitor_id",
    ]
