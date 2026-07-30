"""Normalization policy identifiers for M009.2.6."""
from __future__ import annotations
from enum import Enum


class SuggestionNormalizationPolicy(str, Enum):
    CATALOGUE_DEFAULT = "catalogue_default"

    @classmethod
    def parse(cls, value: object) -> "SuggestionNormalizationPolicy":
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError("normalization_policy must be text or SuggestionNormalizationPolicy.")
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            raise ValueError(f"unsupported normalization policy: {value!r}.") from exc


__all__ = ["SuggestionNormalizationPolicy"]
