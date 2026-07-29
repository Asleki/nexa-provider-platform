import pytest

from registries.metadata import RegistryTrainingEligibility, RegistryTrainingEligibilityError


def test_purpose_codes_are_normalized_deduplicated_and_ordered():
    item = RegistryTrainingEligibility(
        "conditionally_eligible",
        "Controlled purposes",
        purpose_restrictions=(" Research ", "evaluation", "research", "failure_analysis"),
    )
    assert item.purpose_restrictions == (
        "research",
        "evaluation",
        "failure_analysis",
    )


def test_hierarchical_future_domain_purposes_are_supported():
    item = RegistryTrainingEligibility(
        "conditionally_eligible",
        "Simulation uses",
        purpose_restrictions=(
            "simulation.calibration",
            "education.school_planning",
            "financial.failure_analysis",
        ),
    )
    assert item.purpose_restrictions[1] == "education.school_planning"


@pytest.mark.parametrize("value", ["", " ", ".evaluation", "evaluation.", "evaluation..risk", "Evaluation-Only", "evaluation use"])
def test_malformed_purpose_codes_are_rejected(value):
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility(
            "conditionally_eligible",
            "Controlled",
            purpose_restrictions=(value,),
        )


def test_purpose_collection_and_item_types_are_validated():
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("conditionally_eligible", "Controlled", purpose_restrictions="research")
    with pytest.raises(TypeError):
        RegistryTrainingEligibility("conditionally_eligible", "Controlled", purpose_restrictions=(1,))


def test_purpose_code_length_is_bounded():
    with pytest.raises(RegistryTrainingEligibilityError):
        RegistryTrainingEligibility(
            "conditionally_eligible",
            "Controlled",
            purpose_restrictions=("x" * 256,),
        )
