"""Training eligibility states for registry-level policy."""
from enum import Enum
class RegistryTrainingEligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    CONDITIONALLY_ELIGIBLE = "conditionally_eligible"
    INELIGIBLE = "ineligible"
    PROHIBITED = "prohibited"
    UNREVIEWED = "unreviewed"
    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls): return value
        if not isinstance(value, str): raise TypeError("training eligibility status must be text or RegistryTrainingEligibilityStatus.")
        normalized = value.strip().lower()
        if not normalized: raise ValueError("training eligibility status cannot be empty.")
        try: return cls(normalized)
        except ValueError as exc: raise ValueError(f"Unsupported training eligibility status {value!r}.") from exc
    def __str__(self): return self.value
__all__ = ["RegistryTrainingEligibilityStatus"]
