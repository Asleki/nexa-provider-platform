from dataclasses import FrozenInstanceError
import pytest
from registries.name_suggestions.suggestion_duplicate_policy import SuggestionDuplicatePolicy


def test_strict_policy_is_explicit_serializable_and_immutable():
    policy = SuggestionDuplicatePolicy.strict()
    assert policy.to_dict() == {
        "policy_id": "strict",
        "compare_canonical_name_ids": True,
        "compare_normalized_values": True,
        "reject_within_result": True,
    }
    with pytest.raises(FrozenInstanceError):
        policy.policy_id = "other"


def test_alternative_policy_factories_keep_semantics_explicit():
    assert SuggestionDuplicatePolicy.identifiers_only().compare_normalized_values is False
    assert SuggestionDuplicatePolicy.allow_repeated_values().reject_within_result is False
    with pytest.raises(TypeError):
        SuggestionDuplicatePolicy(compare_normalized_values="yes")
