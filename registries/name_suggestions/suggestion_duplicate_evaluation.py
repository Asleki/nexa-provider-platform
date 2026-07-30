"""Immutable duplicate evaluation for M009.2.7."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SuggestionDuplicateEvaluation:
    canonical_name_id: str
    comparison_value: str
    duplicate: bool
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("canonical_name_id", "comparison_value"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty text.")
            object.__setattr__(self, field_name, value.strip())
        if not isinstance(self.duplicate, bool):
            raise TypeError("duplicate must be a bool.")
        reasons = tuple(self.reasons)
        if any(not isinstance(reason, str) or not reason.strip() for reason in reasons):
            raise ValueError("reasons must contain non-empty text values.")
        reasons = tuple(dict.fromkeys(reason.strip() for reason in reasons))
        if self.duplicate != bool(reasons):
            raise ValueError("duplicate must match whether duplicate reasons are present.")
        object.__setattr__(self, "reasons", reasons)

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_name_id": self.canonical_name_id,
            "comparison_value": self.comparison_value,
            "duplicate": self.duplicate,
            "reasons": list(self.reasons),
        }


__all__ = ["SuggestionDuplicateEvaluation"]
