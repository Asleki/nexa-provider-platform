import pytest
from registries.name_suggestions.suggestion_duplicate_evaluation import SuggestionDuplicateEvaluation


def test_duplicate_evaluation_is_consistent_and_serializable():
    evaluation = SuggestionDuplicateEvaluation("name:first:1", "amara", True, ("excluded_name_id",))
    assert evaluation.to_dict()["duplicate"] is True
    assert evaluation.reasons == ("excluded_name_id",)


def test_rejects_mismatched_duplicate_flag_and_reason_state():
    with pytest.raises(ValueError, match="must match"):
        SuggestionDuplicateEvaluation("name:first:1", "amara", False, ("reason",))
    with pytest.raises(ValueError, match="must match"):
        SuggestionDuplicateEvaluation("name:first:1", "amara", True, ())
