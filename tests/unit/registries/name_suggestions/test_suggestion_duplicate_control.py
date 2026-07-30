import pytest
from registries.name_suggestions.first_eligible_selection_policy import FirstEligibleSelectionPolicy
from registries.name_suggestions.suggestion_duplicate_control import DuplicateAwareSelectionPolicy, SuggestionDuplicateControl
from registries.name_suggestions.suggestion_duplicate_policy import SuggestionDuplicatePolicy
from registries.name_suggestions.suggestion_errors import NameSuggestionCandidateNotFoundError
from registries.names import FirstName, MiddleName, NameMetadata


def _first(identifier, value, runtime="simulation"):
    return FirstName(identifier, value, NameMetadata(runtime_mode=runtime)).as_canonical()


def test_detects_id_value_and_within_result_duplicates():
    amara = _first("name:first:amara", "Amara")
    other_kind_same_value = MiddleName("name:middle:amara", "AMARA").as_canonical()
    control = SuggestionDuplicateControl()
    assert control.evaluate(amara, excluded_name_ids=(amara.name_id,)).reasons == ("excluded_name_id",)
    assert control.evaluate(amara, excluded_values=(amara.search_value,)).reasons == ("excluded_normalized_value",)
    assert control.evaluate(other_kind_same_value, selected=(amara,)).reasons == ("selected_normalized_value",)


def test_runtime_and_kind_are_not_implicitly_collapsed_without_matching_exclusion():
    simulation = _first("name:first:sim", "Amara", "simulation")
    production = _first("name:first:prod", "Amara", "production")
    evaluation = SuggestionDuplicateControl(SuggestionDuplicatePolicy.identifiers_only()).evaluate(
        production, selected=(simulation,)
    )
    assert evaluation.duplicate is False


def test_duplicate_aware_selection_filters_and_tracks_selected_records():
    a = _first("name:first:a", "Amina")
    b = _first("name:first:b", "Binta")
    policy = DuplicateAwareSelectionPolicy(
        FirstEligibleSelectionPolicy(),
        SuggestionDuplicateControl(),
        excluded_name_ids=(a.name_id,),
    )
    assert policy.select((a, b)) is b
    assert policy.selected == (b,)
    with pytest.raises(NameSuggestionCandidateNotFoundError):
        policy.select((b,))
