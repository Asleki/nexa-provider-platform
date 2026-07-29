import pytest

from registries.metadata import RegistryRetentionMode


def test_all_stable_retention_mode_values_are_preserved():
    assert {item.name: item.value for item in RegistryRetentionMode} == {
        "PERMANENT": "permanent",
        "FIXED_DURATION": "fixed_duration",
        "UNTIL_DATE": "until_date",
        "EVENT_TRIGGERED": "event_triggered",
        "LEGAL_HOLD": "legal_hold",
        "POLICY_REVIEW_REQUIRED": "policy_review_required",
    }


@pytest.mark.parametrize("member", list(RegistryRetentionMode))
def test_from_value_accepts_existing_members(member):
    assert RegistryRetentionMode.from_value(member) is member


@pytest.mark.parametrize("member", list(RegistryRetentionMode))
def test_from_value_normalises_text(member):
    assert RegistryRetentionMode.from_value(f"  {member.value.upper()}  ") is member
    assert str(member) == member.value


def test_empty_and_unsupported_values_are_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        RegistryRetentionMode.from_value("   ")
    with pytest.raises(ValueError, match="Unsupported retention mode"):
        RegistryRetentionMode.from_value("rebuildable")


def test_wrong_python_type_is_rejected():
    with pytest.raises(TypeError, match="retention mode must be text"):
        RegistryRetentionMode.from_value(7)
