"""Immutable suggestion-layer normalization result for M009.2.6."""
from __future__ import annotations
from dataclasses import dataclass
from .suggestion_normalization_policy import SuggestionNormalizationPolicy


@dataclass(frozen=True, slots=True)
class SuggestionNormalizationResult:
    original_value: str
    canonical_value: str
    comparison_value: str
    policy: SuggestionNormalizationPolicy = SuggestionNormalizationPolicy.CATALOGUE_DEFAULT

    def __post_init__(self) -> None:
        for field_name in ("original_value", "canonical_value", "comparison_value"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be text.")
        if not self.canonical_value:
            raise ValueError("canonical_value cannot be empty.")
        if not self.comparison_value:
            raise ValueError("comparison_value cannot be empty.")
        object.__setattr__(self, "policy", SuggestionNormalizationPolicy.parse(self.policy))

    @property
    def changed(self) -> bool:
        return self.original_value != self.canonical_value

    def to_dict(self) -> dict[str, object]:
        return {
            "original_value": self.original_value,
            "canonical_value": self.canonical_value,
            "comparison_value": self.comparison_value,
            "policy": self.policy.value,
            "changed": self.changed,
        }


__all__ = ["SuggestionNormalizationResult"]
