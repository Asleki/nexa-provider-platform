import pytest

from registries.metadata import RegistryTrainingEligibilityStatus


def test_status_values_and_order_are_stable():
    assert [item.value for item in RegistryTrainingEligibilityStatus] == [
        "eligible",
        "conditionally_eligible",
        "ineligible",
        "prohibited",
        "unreviewed",
    ]


def test_status_from_value_normalizes_text_and_round_trips_members():
    assert RegistryTrainingEligibilityStatus.from_value(" ELIGIBLE ") is RegistryTrainingEligibilityStatus.ELIGIBLE
    item = RegistryTrainingEligibilityStatus.PROHIBITED
    assert RegistryTrainingEligibilityStatus.from_value(item) is item
    assert str(item) == "prohibited"


def test_status_rejects_blank_unsupported_and_wrong_type_values():
    with pytest.raises(ValueError):
        RegistryTrainingEligibilityStatus.from_value("   ")
    with pytest.raises(ValueError):
        RegistryTrainingEligibilityStatus.from_value("approved")
    with pytest.raises(TypeError):
        RegistryTrainingEligibilityStatus.from_value(1)
