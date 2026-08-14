"""P006.7.3 geographic feature recognition contracts.

Recognition records what NNGLA accepts as a geographic subject.  It does not
create natural features and does not own authoritative geometry.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from registries.country.operating_context import RecordEffectScope
from .lifecycle import SpatialLifecycleStatus

class GeographicOriginClass(str, Enum):
    NATURAL = "NATURAL"
    EMERGENT_HUMAN = "EMERGENT_HUMAN"
    LEGAL_CONSTRUCT = "LEGAL_CONSTRUCT"
    REFERENCE = "REFERENCE"

class ProposalOrigin(str, Enum):
    SOURCE_IMPORT = "SOURCE_IMPORT"
    INTERNAL_SIMULATION = "INTERNAL_SIMULATION"
    PRODUCTION_GUEST = "PRODUCTION_GUEST"
    PRODUCTION_DEVELOPER = "PRODUCTION_DEVELOPER"

@dataclass(frozen=True, slots=True)
class FeatureTypeDefinition:
    feature_type_code: str
    feature_family_code: str
    canonical_label: str
    geometry_expectation: str
    origin_class: GeographicOriginClass
    nngla_recognizable: bool
    nngla_creatable: bool
    nameable: bool
    supports_history: bool
    status: str

    def __post_init__(self) -> None:
        if not self.feature_type_code or not self.feature_family_code:
            raise ValueError("feature type code/family are required")
        if self.origin_class is GeographicOriginClass.NATURAL and self.nngla_creatable:
            raise ValueError("NNGLA cannot create natural geography")

@dataclass(frozen=True, slots=True)
class GeographicFeatureRecognition:
    recognition_id: str
    source_feature_id: str
    feature_type_code: str
    source_dataset_id: str
    source_dataset_version: str
    physical_origin_class: GeographicOriginClass
    lifecycle_status: SpatialLifecycleStatus
    recognition_status: str
    source_geometry_reference: str | None
    crs_code: str | None
    runtime_effect_scope: RecordEffectScope
    source_authority: str
    source_basis: str
    candidate_status: str
    proposal_origin: ProposalOrigin = ProposalOrigin.SOURCE_IMPORT

    def __post_init__(self) -> None:
        if not self.recognition_id.startswith("NG-FEAT-"):
            raise ValueError("recognition_id must use NG-FEAT- namespace")
        if not self.source_feature_id or not self.feature_type_code:
            raise ValueError("source feature and type are required")
        if not self.source_dataset_id or not self.source_dataset_version:
            raise ValueError("source dataset identity/version are required")
        if not isinstance(self.runtime_effect_scope, RecordEffectScope):
            object.__setattr__(self, "runtime_effect_scope", RecordEffectScope(str(self.runtime_effect_scope)))

class MemoryGeographicFeatureRepository:
    def __init__(self) -> None:
        self._items: dict[str, GeographicFeatureRecognition] = {}
        self._by_source: dict[str, str] = {}

    def add(self, record: GeographicFeatureRecognition) -> GeographicFeatureRecognition:
        existing = self._items.get(record.recognition_id)
        if existing is not None and existing != record:
            raise ValueError("recognition identifier collision")
        prior_id = self._by_source.get(record.source_feature_id)
        if prior_id is not None and prior_id != record.recognition_id:
            raise ValueError("source feature already recognized by another record")
        self._items[record.recognition_id] = record
        self._by_source[record.source_feature_id] = record.recognition_id
        return record

    def get(self, recognition_id: str) -> GeographicFeatureRecognition | None:
        return self._items.get(recognition_id)

    def by_source(self, source_feature_id: str) -> GeographicFeatureRecognition | None:
        rid = self._by_source.get(source_feature_id)
        return self._items.get(rid) if rid else None

    def all(self) -> tuple[GeographicFeatureRecognition, ...]:
        return tuple(self._items[k] for k in sorted(self._items))

__all__ = ["GeographicOriginClass", "ProposalOrigin", "FeatureTypeDefinition", "GeographicFeatureRecognition", "MemoryGeographicFeatureRepository"]
