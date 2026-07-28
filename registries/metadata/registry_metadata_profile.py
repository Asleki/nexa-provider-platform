"""Aggregate immutable metadata profile associated with one registry."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from .registry_capability import RegistryCapability
from .registry_data_classification import RegistryDataClassification
from .registry_training_eligibility import RegistryTrainingEligibility
from .registry_provenance import RegistryProvenance
from .registry_retention import RegistryRetention
from .registry_metadata_errors import RegistryMetadataProfileError

def _dt(value, name):
    if value is None: return None
    if not isinstance(value, datetime): raise TypeError(f"{name} must be a datetime or None.")
    if value.tzinfo is None or value.utcoffset() is None: raise RegistryMetadataProfileError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True, slots=True)
class RegistryMetadataProfile:
    registry_id: str
    capabilities: tuple[RegistryCapability, ...]
    data_classification: RegistryDataClassification
    training_eligibility: RegistryTrainingEligibility
    provenance: RegistryProvenance
    retention: RegistryRetention
    profile_version: int = 1
    effective_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: datetime | None = None
    review_status: str = "unreviewed"
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.registry_id, str): raise TypeError("registry_id must be text.")
        rid = self.registry_id.strip()
        if not rid: raise RegistryMetadataProfileError("registry_id cannot be empty.")
        object.__setattr__(self, "registry_id", rid)
        caps = tuple(self.capabilities)
        if not all(isinstance(item, RegistryCapability) for item in caps): raise TypeError("capabilities must contain RegistryCapability values.")
        codes = [item.capability_code for item in caps]
        if len(codes) != len(set(codes)): raise RegistryMetadataProfileError("capability codes must be unique within a profile.")
        object.__setattr__(self, "capabilities", caps)
        for name, expected in (("data_classification", RegistryDataClassification), ("training_eligibility", RegistryTrainingEligibility), ("provenance", RegistryProvenance), ("retention", RegistryRetention)):
            if not isinstance(getattr(self, name), expected): raise TypeError(f"{name} must be a {expected.__name__}.")
        if isinstance(self.profile_version, bool) or not isinstance(self.profile_version, int): raise TypeError("profile_version must be an integer.")
        if self.profile_version < 1: raise RegistryMetadataProfileError("profile_version must be at least 1.")
        object.__setattr__(self, "effective_from", _dt(self.effective_from, "effective_from"))
        object.__setattr__(self, "reviewed_at", _dt(self.reviewed_at, "reviewed_at"))
        if not isinstance(self.review_status, str): raise TypeError("review_status must be text.")
        status = self.review_status.strip().lower()
        if status not in {"unreviewed", "approved", "rejected", "conditional"}: raise RegistryMetadataProfileError("unsupported review_status.")
        if status == "unreviewed" and self.reviewed_at is not None: raise RegistryMetadataProfileError("unreviewed profile cannot have reviewed_at.")
        if status != "unreviewed" and self.reviewed_at is None: raise RegistryMetadataProfileError("reviewed profiles require reviewed_at.")
        object.__setattr__(self, "review_status", status)
        if not isinstance(self.attributes, Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def to_dict(self):
        return {"registry_id": self.registry_id, "capabilities": [item.to_dict() for item in self.capabilities],
                "data_classification": self.data_classification.to_dict(),
                "training_eligibility": self.training_eligibility.to_dict(), "provenance": self.provenance.to_dict(),
                "retention": self.retention.to_dict(), "profile_version": self.profile_version,
                "effective_from": self.effective_from.isoformat(),
                "reviewed_at": None if self.reviewed_at is None else self.reviewed_at.isoformat(),
                "review_status": self.review_status, "attributes": dict(self.attributes)}
__all__ = ["RegistryMetadataProfile"]
