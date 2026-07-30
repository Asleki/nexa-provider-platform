"""Policy contract for M009.2.7 duplicate controls."""
from __future__ import annotations
from dataclasses import dataclass


def _policy_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("policy_id must be text.")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("policy_id cannot be empty.")
    return normalized


@dataclass(frozen=True, slots=True)
class SuggestionDuplicatePolicy:
    policy_id: str = "strict"
    compare_canonical_name_ids: bool = True
    compare_normalized_values: bool = True
    reject_within_result: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", _policy_id(self.policy_id))
        for field_name in (
            "compare_canonical_name_ids",
            "compare_normalized_values",
            "reject_within_result",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool.")

    @classmethod
    def strict(cls) -> "SuggestionDuplicatePolicy":
        return cls()

    @classmethod
    def identifiers_only(cls) -> "SuggestionDuplicatePolicy":
        return cls("identifiers_only", True, False, True)

    @classmethod
    def allow_repeated_values(cls) -> "SuggestionDuplicatePolicy":
        return cls("allow_repeated_values", True, False, False)

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "compare_canonical_name_ids": self.compare_canonical_name_ids,
            "compare_normalized_values": self.compare_normalized_values,
            "reject_within_result": self.reject_within_result,
        }


__all__ = ["SuggestionDuplicatePolicy"]
