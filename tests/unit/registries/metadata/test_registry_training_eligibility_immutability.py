from dataclasses import FrozenInstanceError

import pytest

from registries.metadata import RegistryTrainingEligibility, RegistryTrainingEligibilityError


def test_contract_and_nested_extensions_are_immutable_snapshots():
    source = {
        "policy": {
            "reviewers": ["supervisor"],
            "purposes": {"evaluation", "failure_analysis"},
        }
    }
    item = RegistryTrainingEligibility(
        "conditionally_eligible",
        "Reviewed",
        human_approval_required=True,
        attributes=source,
    )
    source["policy"]["reviewers"].append("auditor")
    source["policy"]["purposes"].add("research")
    assert item.attributes["policy"]["reviewers"] == ("supervisor",)
    assert item.attributes["policy"]["purposes"] == frozenset({"evaluation", "failure_analysis"})
    with pytest.raises(FrozenInstanceError):
        item.reason = "Changed"
    with pytest.raises(TypeError):
        item.attributes["new"] = True
    with pytest.raises(TypeError):
        item.attributes["policy"]["reviewers"] += ("auditor",)


def test_attribute_keys_are_text_nonempty_and_unique_after_normalization():
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("unreviewed", "Pending", attributes={1: "bad"})
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility("unreviewed", "Pending", attributes={" ": "bad"})
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility(
            "unreviewed",
            "Pending",
            attributes={"policy": 1, " policy ": 2},
        )


def test_attributes_must_be_a_mapping():
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("unreviewed", "Pending", attributes=[])
