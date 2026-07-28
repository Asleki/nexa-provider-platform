"""Immutable source-lineage declaration for registry metadata."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from .registry_provenance_source_type import RegistryProvenanceSourceType
from .registry_metadata_errors import RegistryProvenanceError

def _dt(value, name):
    if value is None: return None
    if not isinstance(value, datetime): raise TypeError(f"{name} must be a datetime or None.")
    if value.tzinfo is None or value.utcoffset() is None: raise RegistryProvenanceError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True, slots=True)
class RegistryProvenance:
    source_type: RegistryProvenanceSourceType
    source_system: str
    source_reference: str = ""
    source_actor_id: str = ""
    source_institution_id: str = ""
    source_event_id: str = ""
    generated: bool = False
    generator_name: str = ""
    generator_version: str = ""
    generation_batch_id: str = ""
    generation_seed_reference: str = ""
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified: bool = False
    verified_at: datetime | None = None
    verification_reference: str = ""
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "source_type", RegistryProvenanceSourceType.from_value(self.source_type))
        for name in ("source_system", "source_reference", "source_actor_id", "source_institution_id", "source_event_id", "generator_name", "generator_version", "generation_batch_id", "generation_seed_reference", "verification_reference"):
            value = getattr(self, name)
            if not isinstance(value, str): raise TypeError(f"{name} must be text.")
            value = value.strip()
            if name == "source_system" and not value: raise RegistryProvenanceError("source_system cannot be empty.")
            object.__setattr__(self, name, value)
        if not isinstance(self.generated, bool) or not isinstance(self.verified, bool): raise TypeError("generated and verified must be booleans.")
        if self.generated and not (self.generator_name or self.generation_batch_id or self.generation_seed_reference):
            raise RegistryProvenanceError("generated provenance requires generator or generation reference information.")
        object.__setattr__(self, "recorded_at", _dt(self.recorded_at, "recorded_at"))
        object.__setattr__(self, "verified_at", _dt(self.verified_at, "verified_at"))
        if self.verified and self.verified_at is None and not self.verification_reference:
            raise RegistryProvenanceError("verified provenance requires verified_at or verification_reference.")
        if not self.verified and (self.verified_at is not None or self.verification_reference):
            raise RegistryProvenanceError("unverified provenance cannot contain verification details.")
        if isinstance(self.version, bool) or not isinstance(self.version, int): raise TypeError("version must be an integer.")
        if self.version < 1: raise RegistryProvenanceError("version must be at least 1.")
        if not isinstance(self.attributes, Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def to_dict(self):
        return {"source_type": self.source_type.value, "source_system": self.source_system,
                "source_reference": self.source_reference, "source_actor_id": self.source_actor_id,
                "source_institution_id": self.source_institution_id, "source_event_id": self.source_event_id,
                "generated": self.generated, "generator_name": self.generator_name,
                "generator_version": self.generator_version, "generation_batch_id": self.generation_batch_id,
                "generation_seed_reference": self.generation_seed_reference,
                "recorded_at": self.recorded_at.isoformat(), "verified": self.verified,
                "verified_at": None if self.verified_at is None else self.verified_at.isoformat(),
                "verification_reference": self.verification_reference, "version": self.version,
                "attributes": dict(self.attributes)}
__all__ = ["RegistryProvenance"]
