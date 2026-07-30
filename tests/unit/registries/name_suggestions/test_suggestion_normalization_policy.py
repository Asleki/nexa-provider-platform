import pytest
from registries.name_suggestions.suggestion_normalization_policy import SuggestionNormalizationPolicy


def test_parses_default_policy_deterministically():
    assert SuggestionNormalizationPolicy.parse(" CATALOGUE_DEFAULT ") is SuggestionNormalizationPolicy.CATALOGUE_DEFAULT


def test_rejects_unknown_or_non_text_policy():
    with pytest.raises(ValueError):
        SuggestionNormalizationPolicy.parse("accent_stripping")
    with pytest.raises(TypeError):
        SuggestionNormalizationPolicy.parse(1)
