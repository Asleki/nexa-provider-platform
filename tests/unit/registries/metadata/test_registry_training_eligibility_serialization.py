import pytest

from registries.metadata import RegistryTrainingEligibility


def _build_item():
    return RegistryTrainingEligibility(
        "conditionally_eligible",
        "Reviewed synthetic failure evidence",
        anonymisation_required=True,
        human_approval_required=True,
        simulation_only=True,
        purpose_restrictions=("failure_analysis", "evaluation"),
        version=3,
        attributes={"policy": {"reviewers": ["supervisor"]}},
    )


def test_serialization_shape_is_deterministic_and_complete():
    item = _build_item()
    expected = {
        "status": "conditionally_eligible",
        "reason": "Reviewed synthetic failure evidence",
        "anonymisation_required": True,
        "aggregation_required": False,
        "human_approval_required": True,
        "consent_required": False,
        "simulation_only": True,
        "purpose_restrictions": ["failure_analysis", "evaluation"],
        "version": 3,
        "attributes": {"policy": {"reviewers": ["supervisor"]}},
    }
    assert item.to_dict() == expected
    assert item.to_dict() == expected


def test_round_trip_reconstructs_equal_contract():
    item = _build_item()
    assert RegistryTrainingEligibility.from_dict(item.to_dict()) == item


def test_from_dict_detaches_caller_owned_input():
    payload = _build_item().to_dict()
    item = RegistryTrainingEligibility.from_dict(payload)
    payload["purpose_restrictions"].append("research")
    payload["attributes"]["policy"]["reviewers"].append("auditor")
    assert item.purpose_restrictions == ("failure_analysis", "evaluation")
    assert item.attributes["policy"]["reviewers"] == ("supervisor",)


def test_serialized_output_is_detached_from_contract():
    item = _build_item()
    payload = item.to_dict()
    payload["purpose_restrictions"].append("research")
    payload["attributes"]["policy"]["reviewers"].append("auditor")
    assert item.purpose_restrictions == ("failure_analysis", "evaluation")
    assert item.attributes["policy"]["reviewers"] == ("supervisor",)


def test_from_dict_requires_mapping():
    with pytest.raises(TypeError):
        RegistryTrainingEligibility.from_dict([])
