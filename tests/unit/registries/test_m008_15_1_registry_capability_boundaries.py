from dataclasses import fields

from registries.metadata import RegistryCapability


def test_capability_contract_does_not_absorb_later_milestone_responsibilities():
    field_names = {item.name for item in fields(RegistryCapability)}
    forbidden = {
        "permission",
        "approval",
        "classification",
        "training_eligibility",
        "provenance",
        "retention",
        "relationships",
        "payload_schema",
        "execution_handler",
    }
    assert field_names.isdisjoint(forbidden)


def test_future_domains_share_one_contract_without_domain_specific_fields():
    capabilities = (
        RegistryCapability("birth-v1", "CIVIL.BIRTH.RECORD.REGISTER", "Register Birth", "identity"),
        RegistryCapability("school-v1", "EDUCATION.SCHOOL.REGISTER", "Register School", "identity"),
        RegistryCapability("gdp-v1", "MONETARY.ECONOMIC_METRIC.GDP_PUBLISH", "Publish GDP", "export"),
        RegistryCapability("weather-v1", "ENVIRONMENT.WEATHER.OBSERVE", "Observe Weather", "simulation"),
    )
    assert all(type(item) is RegistryCapability for item in capabilities)
