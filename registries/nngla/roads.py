"""P006.7.6 governed road-reference and canonical-road contracts."""
from __future__ import annotations
from dataclasses import dataclass
import re
from registries.country.operating_context import RecordEffectScope

@dataclass(frozen=True, slots=True)
class RoadClassificationDefinition:
    road_class_code: str
    canonical_label: str
    administrative_level: str
    access_scope: str
    intended_function: str
    nameable: bool
    addressable: bool
    parcel_access_eligible: bool
    status: str
    description: str
    def __post_init__(self) -> None:
        if not self.road_class_code or not self.canonical_label: raise ValueError("road class identity/label required")
        if self.status != "ACTIVE": raise ValueError("Bundle 15B accepts active governed road classes")

@dataclass(frozen=True, slots=True)
class RoadReferenceCandidate:
    road_candidate_id: str
    road_name_id: str
    canonical_name: str
    road_class_code: str
    source_name_family: str
    planning_status: str
    geometry_status: str
    geometry_reference: str | None
    addressing_eligible: bool
    region_code: str | None
    source_basis: str
    runtime_effect_scope: RecordEffectScope | str
    def __post_init__(self) -> None:
        if not re.fullmatch(r"NG-RD-CAND-\d{6}",self.road_candidate_id): raise ValueError("road candidate identity invalid")
        if not re.fullmatch(r"NG-NAM-ROA-\d{6}",self.road_name_id): raise ValueError("road name must use governed geographic-name road identity")
        if not self.road_class_code or not self.canonical_name: raise ValueError("road class and canonical name required")
        if self.region_code is not None and not self.region_code.startswith("NGR-"): raise ValueError("region reference must use NGR identity")
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        object.__setattr__(self,"runtime_effect_scope",scope)
    @property
    def is_constructed_or_mapped(self):
        return self.geometry_status not in {"UNMAPPED_PENDING_CONSTRUCTION_OR_SURVEY","UNMAPPED"}

@dataclass(frozen=True, slots=True)
class CanonicalRoad:
    road_id: str
    source_candidate_id: str
    road_name_id: str
    road_class_code: str
    geometry_id: str | None
    lifecycle_status: str
    runtime_effect_scope: RecordEffectScope | str
    def __post_init__(self) -> None:
        if not re.fullmatch(r"NG-RD-\d{6}",self.road_id): raise ValueError("road_id must use governed NG-RD-###### identity")
        if not re.fullmatch(r"NG-RD-CAND-\d{6}",self.source_candidate_id): raise ValueError("source candidate identity invalid")
        if not re.fullmatch(r"NG-NAM-ROA-\d{6}",self.road_name_id): raise ValueError("road_name_id invalid")
        if self.geometry_id is not None and not re.fullmatch(r"NG-GEO-\d{6}",self.geometry_id): raise ValueError("geometry_id invalid")
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        object.__setattr__(self,"runtime_effect_scope",scope)

class MemoryRoadRepository:
    def __init__(self): self._items: dict[str,CanonicalRoad]={}
    def add(self,road:CanonicalRoad):
        p=self._items.get(road.road_id)
        if p is not None and p != road: raise ValueError("road identifier collision")
        self._items[road.road_id]=road; return road
    def get(self,road_id): return self._items.get(road_id)
    def all(self): return tuple(self._items[k] for k in sorted(self._items))

__all__=["RoadClassificationDefinition","RoadReferenceCandidate","CanonicalRoad","MemoryRoadRepository"]
