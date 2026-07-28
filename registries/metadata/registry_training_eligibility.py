"""Immutable registry-level AI training eligibility declaration."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from .registry_training_eligibility_status import RegistryTrainingEligibilityStatus
from .registry_metadata_errors import RegistryTrainingEligibilityError

@dataclass(frozen=True, slots=True)
class RegistryTrainingEligibility:
    status: RegistryTrainingEligibilityStatus
    reason: str
    anonymisation_required: bool = False
    aggregation_required: bool = False
    human_approval_required: bool = False
    consent_required: bool = False
    simulation_only: bool = False
    purpose_restrictions: tuple[str, ...] = field(default_factory=tuple)
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "status", RegistryTrainingEligibilityStatus.from_value(self.status))
        if not isinstance(self.reason, str): raise TypeError("reason must be text.")
        reason = self.reason.strip()
        if not reason: raise RegistryTrainingEligibilityError("reason cannot be empty.")
        object.__setattr__(self, "reason", reason)
        for name in ("anonymisation_required", "aggregation_required", "human_approval_required", "consent_required", "simulation_only"):
            if not isinstance(getattr(self, name), bool): raise TypeError(f"{name} must be a boolean.")
        if isinstance(self.purpose_restrictions, (str, bytes)): raise TypeError("purpose_restrictions must be an iterable of text values.")
        restrictions = []
        for item in self.purpose_restrictions:
            if not isinstance(item, str): raise TypeError("purpose_restrictions must contain text values.")
            item = item.strip()
            if not item: raise RegistryTrainingEligibilityError("purpose restrictions cannot be empty.")
            if item not in restrictions: restrictions.append(item)
        object.__setattr__(self, "purpose_restrictions", tuple(restrictions))
        if self.status is RegistryTrainingEligibilityStatus.ELIGIBLE and any((self.anonymisation_required, self.aggregation_required, self.human_approval_required, self.consent_required, self.purpose_restrictions)):
            raise RegistryTrainingEligibilityError("unconditional ELIGIBLE status cannot declare eligibility conditions.")
        if self.status in (RegistryTrainingEligibilityStatus.INELIGIBLE, RegistryTrainingEligibilityStatus.PROHIBITED, RegistryTrainingEligibilityStatus.UNREVIEWED) and self.simulation_only:
            raise RegistryTrainingEligibilityError("simulation_only requires an eligible or conditionally eligible status.")
        if isinstance(self.version, bool) or not isinstance(self.version, int): raise TypeError("version must be an integer.")
        if self.version < 1: raise RegistryTrainingEligibilityError("version must be at least 1.")
        if not isinstance(self.attributes, Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    @property
    def may_be_considered(self):
        return self.status in (RegistryTrainingEligibilityStatus.ELIGIBLE, RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE)

    def to_dict(self):
        return {"status": self.status.value, "reason": self.reason, "anonymisation_required": self.anonymisation_required,
                "aggregation_required": self.aggregation_required, "human_approval_required": self.human_approval_required,
                "consent_required": self.consent_required, "simulation_only": self.simulation_only,
                "purpose_restrictions": list(self.purpose_restrictions), "version": self.version,
                "attributes": dict(self.attributes)}
    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise TypeError("data must be a mapping.")
        return cls(**dict(data))
__all__ = ["RegistryTrainingEligibility"]
