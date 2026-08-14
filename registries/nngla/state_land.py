"""P006.7.8 governed state-land ownership/control classification contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import re
from registries.country.operating_context import RecordEffectScope

@dataclass(frozen=True,slots=True)
class StateLandCategoryDefinition:
    state_land_category_code:str
    canonical_label:str
    purpose:str
    allocatable:bool
    leaseable:str
    protected:bool
    status:str
    description:str
    def __post_init__(self) -> None:
        if not self.state_land_category_code or not self.canonical_label: raise ValueError('state-land category identity/label required')
        if self.leaseable not in {'true','false','limited'}: raise ValueError('leaseable must preserve governed true/false/limited semantics')
        if self.status!='ACTIVE': raise ValueError('Bundle 15C accepts active governed state-land categories')

@dataclass(frozen=True,slots=True)
class StateLandRecord:
    state_land_record_id:str
    parcel_id:str
    state_land_category_code:str
    administrative_area_id:str|None
    status:str
    effective_from:date
    effective_to:date|None
    source_reference:str
    runtime_effect_scope:RecordEffectScope|str=RecordEffectScope.RUNTIME_SCOPED
    def __post_init__(self) -> None:
        if not self.state_land_record_id: raise ValueError('state_land_record_id is required')
        if any(c.isspace() for c in self.state_land_record_id): raise ValueError('state_land_record_id must be opaque without whitespace')
        if not re.fullmatch(r'NV-\d{2}-\d{3}-\d{4,}',self.parcel_id): raise ValueError('parcel_id invalid')
        if not self.state_land_category_code: raise ValueError('state_land_category_code required')
        if self.administrative_area_id is not None and not self.administrative_area_id: raise ValueError('administrative_area_id cannot be blank')
        if not self.status: raise ValueError('state land status required')
        if self.effective_to is not None and self.effective_to < self.effective_from: raise ValueError('effective_to cannot precede effective_from')
        if not self.source_reference: raise ValueError('source_reference required')
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        if scope is not RecordEffectScope.RUNTIME_SCOPED: raise ValueError('state-land operational effect must remain RUNTIME_SCOPED')
        object.__setattr__(self,'runtime_effect_scope',scope)

class MemoryStateLandRepository:
    def __init__(self): self._items:dict[str,StateLandRecord]={}
    def add(self,record:StateLandRecord):
        p=self._items.get(record.state_land_record_id)
        if p is not None and p!=record: raise ValueError('state-land record identity collision')
        self._items[record.state_land_record_id]=record; return record
    def get(self,record_id): return self._items.get(record_id)
    def for_parcel(self,parcel_id): return tuple(r for r in self._items.values() if r.parcel_id==parcel_id)
    def all(self): return tuple(self._items[k] for k in sorted(self._items))

__all__=['StateLandCategoryDefinition','StateLandRecord','MemoryStateLandRepository']
