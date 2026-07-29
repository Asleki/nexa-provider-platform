import pytest

from registries.metadata import (
    RegistryTrainingEligibility,
    RegistryTrainingEligibilityError,
    RegistryTrainingEligibilityStatus,
)


def test_reason_is_required_normalized_and_bounded():
    item = RegistryTrainingEligibility("unreviewed", "  Pending policy review  ")
    assert item.reason == "Pending policy review"
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility("unreviewed", "  ")
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility("unreviewed", "x" * 2001)
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("unreviewed", 42)


def test_boolean_fields_are_strict():
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("conditionally_eligible", "Review", human_approval_required=1)


def test_conditional_status_requires_at_least_one_condition():
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility("conditionally_eligible", "Controlled use")


def test_conditional_status_accepts_each_supported_condition():
    assert RegistryTrainingEligibility("conditionally_eligible", "Anon", anonymisation_required=True).may_be_considered
    assert RegistryTrainingEligibility("conditionally_eligible", "Aggregate", aggregation_required=True).may_be_considered
    assert RegistryTrainingEligibility("conditionally_eligible", "Review", human_approval_required=True).may_be_considered
    assert RegistryTrainingEligibility("conditionally_eligible", "Consent", consent_required=True).may_be_considered
    assert RegistryTrainingEligibility("conditionally_eligible", "Simulation", simulation_only=True).may_be_considered
    assert RegistryTrainingEligibility("conditionally_eligible", "Evaluation", purpose_restrictions=("evaluation",)).may_be_considered


@pytest.mark.parametrize("status", ["ineligible", "prohibited", "unreviewed"])
def test_blocked_statuses_reject_all_eligibility_conditions(status):
    kwargs = [
        {"anonymisation_required": True},
        {"aggregation_required": True},
        {"human_approval_required": True},
        {"consent_required": True},
        {"simulation_only": True},
        {"purpose_restrictions": ("evaluation",)},
    ]
    for condition in kwargs:
        with pytest.raises(RegistryTrainingEligibilityError):
            RegistryTrainingEligibility(status, "Blocked", **condition)


def test_eligible_is_unconditional_inside_its_scope():
    item = RegistryTrainingEligibility("eligible", "Synthetic evidence", simulation_only=True)
    assert item.status is RegistryTrainingEligibilityStatus.ELIGIBLE
    assert item.simulation_only is True
    assert item.may_be_considered is True
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility("eligible", "Needs approval", human_approval_required=True)


def test_may_be_considered_is_conservative():
    assert RegistryTrainingEligibility("eligible", "Approved").may_be_considered
    assert RegistryTrainingEligibility("conditionally_eligible", "Review", human_approval_required=True).may_be_considered
    assert not RegistryTrainingEligibility("ineligible", "Not useful").may_be_considered
    assert not RegistryTrainingEligibility("prohibited", "Forbidden").may_be_considered
    assert not RegistryTrainingEligibility("unreviewed", "Pending").may_be_considered


def test_version_rules_are_strict():
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("unreviewed", "Pending", version=True)
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("unreviewed", "Pending", version=1.0)
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility("unreviewed", "Pending", version=0)


def test_invalid_status_is_translated_to_domain_error():
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility("unknown", "Invalid")
    with pytest.raises(TypeError):
        RegistryTrainingEligibility(123, "Invalid")
