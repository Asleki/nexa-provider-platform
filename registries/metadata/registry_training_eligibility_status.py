"""Stable training-eligibility states for registry-level AI governance."""
from __future__ import annotations

from enum import Enum


class RegistryTrainingEligibilityStatus(str, Enum):
    """Canonical status of a registry's data for future training consideration."""

    ELIGIBLE = "eligible"
    CONDITIONALLY_ELIGIBLE = "conditionally_eligible"
    INELIGIBLE = "ineligible"
    PROHIBITED = "prohibited"
    UNREVIEWED = "unreviewed"

    @classmethod
    def from_value(
        cls,
        value: "RegistryTrainingEligibilityStatus | str",
    ) -> "RegistryTrainingEligibilityStatus":
        """Return a canonical status from an enum member or persisted text value."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError(
                "training eligibility status must be text or "
                "RegistryTrainingEligibilityStatus."
            )
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("training eligibility status cannot be empty.")
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported training eligibility status {value!r}."
            ) from exc

    def __str__(self) -> str:
        return self.value


__all__ = ["RegistryTrainingEligibilityStatus"]
