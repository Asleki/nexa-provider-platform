"""P006.7.6 addressable-site boundary.

No sovereign NNGLA site-code namespace has yet been issued by the validated
authority pack. `site_id` is therefore an opaque stable reference contract;
this milestone deliberately does not invent a new NG-* identifier family.
"""
from __future__ import annotations
from dataclasses import dataclass
from registries.country.operating_context import RecordEffectScope

@dataclass(frozen=True, slots=True)
class AddressableSiteReference:
    site_id: str
    place_id: str | None
    administrative_area_id: str | None
    road_id: str | None
    parcel_id: str | None
    geometry_reference: str | None
    site_status: str
    runtime_effect_scope: RecordEffectScope | str
    def __post_init__(self) -> None:
        if not isinstance(self.site_id,str) or not self.site_id.strip(): raise ValueError("site_id is required")
        if self.road_id is not None and not self.road_id.startswith("NG-RD-"): raise ValueError("road reference must use NNGLA road identity")
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        object.__setattr__(self,"runtime_effect_scope",scope)

class MemoryAddressableSiteRepository:
    def __init__(self): self._items: dict[str,AddressableSiteReference]={}
    def add(self,site):
        p=self._items.get(site.site_id)
        if p is not None and p != site: raise ValueError("site identifier collision")
        self._items[site.site_id]=site; return site
    def get(self,site_id): return self._items.get(site_id)
    def all(self): return tuple(self._items[k] for k in sorted(self._items))

__all__=["AddressableSiteReference","MemoryAddressableSiteRepository"]
