import pytest
from registries.name_suggestions.suggestion_name_normalizer import SuggestionNameNormalizer


def test_reuses_catalogue_normalization_and_comparison_rules():
    result = SuggestionNameNormalizer().normalize("  AＭＡＲＡ   Njeri  ")
    assert result.original_value == "  AＭＡＲＡ   Njeri  "
    assert result.canonical_value == "AＭＡＲＡ Njeri"
    assert result.comparison_value == "amara njeri"
    assert result.changed is True


def test_repeated_calls_are_deterministic_and_invalid_input_is_rejected():
    normalizer = SuggestionNameNormalizer()
    assert normalizer.normalize("Élodie") == normalizer.normalize("Élodie")
    with pytest.raises(TypeError):
        normalizer.normalize(None)
    with pytest.raises(ValueError):
        normalizer.normalize("   ")
