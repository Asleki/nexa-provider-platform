from dataclasses import FrozenInstanceError
import pytest
from registries.name_suggestions.suggestion_normalization_result import SuggestionNormalizationResult


def test_preserves_original_and_reports_change_and_serialization():
    result = SuggestionNormalizationResult("  Amara ", "Amara", "amara")
    assert result.changed is True
    assert result.to_dict() == {
        "original_value": "  Amara ",
        "canonical_value": "Amara",
        "comparison_value": "amara",
        "policy": "catalogue_default",
        "changed": True,
    }


def test_is_immutable_and_rejects_empty_comparison_values():
    result = SuggestionNormalizationResult("Amara", "Amara", "amara")
    with pytest.raises(FrozenInstanceError):
        result.canonical_value = "Other"
    with pytest.raises(ValueError):
        SuggestionNormalizationResult("A", "A", "")
