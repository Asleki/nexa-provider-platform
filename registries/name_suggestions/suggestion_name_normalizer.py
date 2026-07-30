"""Catalogue-compatible name normalizer for M009.2.6."""
from __future__ import annotations
from registries.names.canonical_name import comparison_key, normalize_name_value
from .suggestion_normalization_policy import SuggestionNormalizationPolicy
from .suggestion_normalization_result import SuggestionNormalizationResult


class SuggestionNameNormalizer:
    def normalize(
        self,
        value: object,
        policy: SuggestionNormalizationPolicy = SuggestionNormalizationPolicy.CATALOGUE_DEFAULT,
    ) -> SuggestionNormalizationResult:
        parsed_policy = SuggestionNormalizationPolicy.parse(policy)
        if not isinstance(value, str):
            raise TypeError("value must be text.")
        canonical = normalize_name_value(value)
        return SuggestionNormalizationResult(
            original_value=value,
            canonical_value=canonical,
            comparison_value=comparison_key(canonical),
            policy=parsed_policy,
        )


__all__ = ["SuggestionNameNormalizer"]
