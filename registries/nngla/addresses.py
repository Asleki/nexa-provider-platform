"""P006.7.6 governed address identity/lifecycle contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import re
from registries.country.operating_context import RecordEffectScope

@dataclass(frozen=True, slots=True)
class AddressReferenceCandidate:
    address_candidate_id: str
    street_id: str | None
    address_series: str | None
    premise_sequence: str | None
    unit_designator: str | None
    display_address_number: str | None
    place_id: str | None
    administrative_area_id: str | None
    parcel_id: str | None
    allocation_status: str
    address_status: str
    reserved_at: datetime | None
    assigned_at: datetime | None
    retired_at: datetime | None
    source_reference: str
    runtime_effect_scope: RecordEffectScope | str
    def __post_init__(self) -> None:
        if not self.address_candidate_id: raise ValueError("address candidate identity required")
        if self.assigned_at and self.reserved_at and self.assigned_at < self.reserved_at: raise ValueError("assigned_at cannot precede reserved_at")
        if self.retired_at and self.assigned_at and self.retired_at < self.assigned_at: raise ValueError("retired_at cannot precede assigned_at")
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        object.__setattr__(self,"runtime_effect_scope",scope)

@dataclass(frozen=True, slots=True)
class CanonicalAddress:
    address_id: str
    site_id: str
    road_id: str | None
    display_address_number: str
    unit_designator: str | None
    lifecycle_status: str
    runtime_effect_scope: RecordEffectScope | str
    def __post_init__(self) -> None:
        if not re.fullmatch(r"NG-ADR-\d{6}",self.address_id): raise ValueError("address_id must use governed NG-ADR-###### identity")
        if not self.site_id: raise ValueError("address must reference an addressable site")
        if self.road_id is not None and not re.fullmatch(r"NG-RD-\d{6}",self.road_id): raise ValueError("road_id invalid")
        if not self.display_address_number: raise ValueError("display address number required")
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        object.__setattr__(self,"runtime_effect_scope",scope)

class MemoryAddressRepository:
    def __init__(self): self._items: dict[str,CanonicalAddress]={}
    def add(self,address):
        p=self._items.get(address.address_id)
        if p is not None and p != address: raise ValueError("address identifier collision")
        self._items[address.address_id]=address; return address
    def get(self,address_id): return self._items.get(address_id)
    def all(self): return tuple(self._items[k] for k in sorted(self._items))

__all__=["AddressReferenceCandidate","CanonicalAddress","MemoryAddressRepository"]
