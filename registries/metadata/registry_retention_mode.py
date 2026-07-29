"""Canonical modes for registry retention policy declarations."""
from __future__ import annotations

from enum import Enum


class RegistryRetentionMode(str, Enum):
    """Stable persisted identities for registry retention declarations.

    The enum describes the governing retention shape.  It does not execute
    archival, deletion, legal review, storage movement, or policy evaluation.
    """

    PERMANENT = "permanent"
    FIXED_DURATION = "fixed_duration"
    UNTIL_DATE = "until_date"
    EVENT_TRIGGERED = "event_triggered"
    LEGAL_HOLD = "legal_hold"
    POLICY_REVIEW_REQUIRED = "policy_review_required"

    @classmethod
    def from_value(
        cls,
        value: "RegistryRetentionMode | str",
    ) -> "RegistryRetentionMode":
        """Return a canonical mode from an enum member or text value."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError(
                "retention mode must be text or RegistryRetentionMode."
            )
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("retention mode cannot be empty.")
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported retention mode {value!r}.") from exc

    def __str__(self) -> str:
        return self.value


__all__ = ["RegistryRetentionMode"]
