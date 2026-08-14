"""P006.7.4 non-spatial NoveGeo place-reference contracts."""
from __future__ import annotations
from dataclasses import dataclass
from registries.country.operating_context import RecordEffectScope
from .lifecycle import SpatialLifecycleStatus

@dataclass(frozen=True, slots=True)
class PlaceReference:
    source_place_code: str
    settlement_name_record_id: str
    canonical_name: str
    place_slug: str
    place_type_code: str
    settlement_scale: str
    urbanity: str
    parent_source_place_code: str | None
    major_city_source_place_code: str | None
    region_code: str
    region_name: str
    is_national_capital: bool
    is_regional_anchor: bool
    nickname: str | None
    naming_status_code: str
    lifecycle_status: SpatialLifecycleStatus
    spatial_assignment_status: str
    source_dataset_id: str
    runtime_effect_scope: RecordEffectScope
    record_status: str

    def __post_init__(self) -> None:
        if not self.source_place_code.startswith("NGP-"):
            raise ValueError("source_place_code must preserve NGP PLACE_SOURCE identity")
        if not self.settlement_name_record_id.startswith("NG-NAM-SET-"):
            raise ValueError("settlement name must use NG-NAM-SET identity")
        if not self.region_code.startswith("NGR-"):
            raise ValueError("region_code must use NGR identity")
        if not isinstance(self.runtime_effect_scope, RecordEffectScope):
            object.__setattr__(self, "runtime_effect_scope", RecordEffectScope(str(self.runtime_effect_scope)))
        if self.runtime_effect_scope is not RecordEffectScope.SHARED_REFERENCE:
            raise ValueError("place source catalogue is a shared reference")

    @property
    def has_authoritative_geometry(self) -> bool:
        return self.spatial_assignment_status not in {"UNMAPPED_PENDING_ASSOCIATION", "UNMAPPED"}

class MemoryPlaceRepository:
    def __init__(self) -> None:
        self._items: dict[str, PlaceReference] = {}

    def add(self, place: PlaceReference) -> PlaceReference:
        prior = self._items.get(place.source_place_code)
        if prior is not None and prior != place:
            raise ValueError("source place identifier collision")
        self._items[place.source_place_code] = place
        return place

    def get(self, source_place_code: str) -> PlaceReference | None:
        return self._items.get(source_place_code)

    def children_of(self, source_place_code: str) -> tuple[PlaceReference, ...]:
        return tuple(sorted((p for p in self._items.values() if p.parent_source_place_code == source_place_code), key=lambda p: p.source_place_code))

    def all(self) -> tuple[PlaceReference, ...]:
        return tuple(self._items[k] for k in sorted(self._items))

__all__ = ["PlaceReference", "MemoryPlaceRepository"]
