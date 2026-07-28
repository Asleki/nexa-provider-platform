import pytest

from registries.metadata import RegistryDataClassification


def test_to_dict_returns_complete_deterministic_detached_shape():
    item = RegistryDataClassification(
        level="restricted",
        reason="Citizen and school reference data",
        contains_personal_data=True,
        contains_minor_data=True,
        masking_required=True,
        version=3,
        data_categories=("PERSONAL.IDENTITY", "EDUCATION.STUDENT"),
        attributes={"policy": {"codes": ["P-001", "P-002"]}},
    )

    assert item.to_dict() == {
        "level": "restricted",
        "reason": "Citizen and school reference data",
        "contains_personal_data": True,
        "contains_sensitive_personal_data": False,
        "contains_financial_data": False,
        "contains_health_data": False,
        "contains_minor_data": True,
        "public_disclosure_allowed": False,
        "masking_required": True,
        "version": 3,
        "data_categories": ["PERSONAL.IDENTITY", "EDUCATION.STUDENT"],
        "attributes": {"policy": {"codes": ["P-001", "P-002"]}},
    }


def test_from_dict_round_trip_preserves_contract_values():
    source = {
        "level": "confidential",
        "reason": "Medical and financial records",
        "contains_personal_data": True,
        "contains_sensitive_personal_data": True,
        "contains_financial_data": True,
        "contains_health_data": True,
        "contains_minor_data": False,
        "public_disclosure_allowed": False,
        "masking_required": True,
        "version": 2,
        "data_categories": ["HEALTH.CLINICAL", "FINANCIAL.ACCOUNT"],
        "attributes": {"jurisdictions": ["NOVEGEO"]},
    }

    item = RegistryDataClassification.from_dict(source)
    assert item.to_dict() == source


def test_from_dict_does_not_retain_caller_owned_nested_values():
    source = {
        "level": "restricted",
        "reason": "Subscriber information",
        "data_categories": ["TELECOM.SUBSCRIBER"],
        "attributes": {"policy": {"codes": ["TEL-001"]}},
    }
    item = RegistryDataClassification.from_dict(source)

    source["data_categories"].append("PERSONAL.CONTACT")
    source["attributes"]["policy"]["codes"].append("TEL-002")

    assert item.data_categories == ("TELECOM.SUBSCRIBER",)
    assert item.to_dict()["attributes"] == {"policy": {"codes": ["TEL-001"]}}


def test_mutating_serialized_output_does_not_mutate_contract():
    item = RegistryDataClassification(
        level="restricted",
        reason="Registry information",
        data_categories=("PERSONAL.IDENTITY",),
        attributes={"nested": {"items": ["one"]}},
    )

    serialized = item.to_dict()
    serialized["data_categories"].append("PERSONAL.CONTACT")
    serialized["attributes"]["nested"]["items"].append("two")

    assert item.data_categories == ("PERSONAL.IDENTITY",)
    assert item.to_dict()["attributes"] == {"nested": {"items": ["one"]}}


def test_from_dict_requires_mapping_input():
    for value in (None, [], "classification"):
        with pytest.raises(TypeError, match="data must be a mapping"):
            RegistryDataClassification.from_dict(value)
