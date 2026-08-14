"""P006.7.4 non-spatial administrative-area contracts."""
from __future__ import annotations
from dataclasses import dataclass
from registries.country.operating_context import RecordEffectScope
from .lifecycle import SpatialLifecycleStatus

@dataclass(frozen=True, slots=True)
class AdministrativeArea:
    administrative_candidate_id: str
    source_record_id: str
    administrative_type_code: str
    canonical_name: str
    parent_source_record_id: str
    region_code: str
    boundary_status: str
    geometry_reference: str | None
    lifecycle_status: SpatialLifecycleStatus
    runtime_effect_scope: RecordEffectScope
    source_basis: str
    candidate_status: str

    def __post_init__(self) -> None:
        if not self.administrative_candidate_id.startswith("NG-ADM-CAND-"):
            raise ValueError("administrative_candidate_id must use NG-ADM-CAND namespace")
        if not self.source_record_id or not self.parent_source_record_id:
            raise ValueError("source and parent references are required")
        if not self.region_code.startswith("NGR-"):
            raise ValueError("region_code must use NGR identity")
        if not isinstance(self.runtime_effect_scope, RecordEffectScope):
            object.__setattr__(self, "runtime_effect_scope", RecordEffectScope(str(self.runtime_effect_scope)))

    @property
    def is_nonspatial_ready(self) -> bool:
        return self.candidate_status == "READY_NONSPATIAL" and not self.geometry_reference

class MemoryAdministrativeAreaRepository:
    def __init__(self) -> None:
        self._items: dict[str, AdministrativeArea] = {}
        self._by_source: dict[str, str] = {}

    def add(self, area: AdministrativeArea) -> AdministrativeArea:
        prior = self._items.get(area.administrative_candidate_id)
        if prior is not None and prior != area:
            raise ValueError("administrative candidate identifier collision")
        source_prior = self._by_source.get(area.source_record_id)
        if source_prior is not None and source_prior != area.administrative_candidate_id:
            raise ValueError("source administrative record already represented")
        self._items[area.administrative_candidate_id] = area
        self._by_source[area.source_record_id] = area.administrative_candidate_id
        return area

    def by_source(self, source_record_id: str) -> AdministrativeArea | None:
        rid = self._by_source.get(source_record_id)
        return self._items.get(rid) if rid else None

    def all(self) -> tuple[AdministrativeArea, ...]:
        return tuple(self._items[k] for k in sorted(self._items))

__all__ = ["AdministrativeArea", "MemoryAdministrativeAreaRepository"]
