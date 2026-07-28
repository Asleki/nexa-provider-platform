import pytest
from registries.metadata import RegistryTrainingEligibility, RegistryTrainingEligibilityStatus, RegistryTrainingEligibilityError

def test_conditional_training_policy_is_explicit():
    item = RegistryTrainingEligibility("conditionally_eligible", "Aggregate only", aggregation_required=True, human_approval_required=True, purpose_restrictions=("research", "research"))
    assert item.status is RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE
    assert item.may_be_considered and item.purpose_restrictions == ("research",)

def test_unconditional_eligible_rejects_conditions():
    with pytest.raises(RegistryTrainingEligibilityError): RegistryTrainingEligibility("eligible", "Allowed", anonymisation_required=True)
