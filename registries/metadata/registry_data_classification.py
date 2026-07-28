"""Immutable registry-level data classification declaration."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from .registry_classification_level import RegistryClassificationLevel
from .registry_metadata_errors import RegistryClassificationError

@dataclass(frozen=True, slots=True)
class RegistryDataClassification:
    level: RegistryClassificationLevel
    reason: str
    contains_personal_data: bool = False
    contains_sensitive_personal_data: bool = False
    contains_financial_data: bool = False
    contains_health_data: bool = False
    contains_minor_data: bool = False
    public_disclosure_allowed: bool = False
    masking_required: bool = False
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "level", RegistryClassificationLevel.from_value(self.level))
        if not isinstance(self.reason, str): raise TypeError("reason must be text.")
        reason = self.reason.strip()
        if not reason: raise RegistryClassificationError("reason cannot be empty.")
        object.__setattr__(self, "reason", reason)
        flags = ("contains_personal_data", "contains_sensitive_personal_data", "contains_financial_data", "contains_health_data", "contains_minor_data", "public_disclosure_allowed", "masking_required")
        for name in flags:
            if not isinstance(getattr(self, name), bool): raise TypeError(f"{name} must be a boolean.")
        if self.contains_sensitive_personal_data and not self.contains_personal_data:
            raise RegistryClassificationError("sensitive personal data requires contains_personal_data=True.")
        if self.level >= RegistryClassificationLevel.CONFIDENTIAL and self.public_disclosure_allowed:
            raise RegistryClassificationError("confidential or stronger data cannot allow public disclosure.")
        if self.level is RegistryClassificationLevel.PUBLIC and self.masking_required:
            raise RegistryClassificationError("public classification cannot require masking.")
        if isinstance(self.version, bool) or not isinstance(self.version, int): raise TypeError("version must be an integer.")
        if self.version < 1: raise RegistryClassificationError("version must be at least 1.")
        if not isinstance(self.attributes, Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def to_dict(self):
        result = {name: getattr(self, name) for name in (
            "reason", "contains_personal_data", "contains_sensitive_personal_data", "contains_financial_data",
            "contains_health_data", "contains_minor_data", "public_disclosure_allowed", "masking_required", "version")}
        return {"level": self.level.code, **result, "attributes": dict(self.attributes)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise TypeError("data must be a mapping.")
        return cls(**dict(data))

__all__ = ["RegistryDataClassification"]
