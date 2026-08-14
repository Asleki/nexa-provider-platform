"""P006.7.8 governed title identity, holder-reference and lifecycle contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
import re
from registries.country.operating_context import RecordEffectScope

class TitleStatus(str,Enum):
    DRAFT='DRAFT'; ISSUED='ISSUED'; ACTIVE='ACTIVE'; TRANSFERRED='TRANSFERRED'; ENCUMBERED='ENCUMBERED'
    SUSPENDED='SUSPENDED'; CANCELLED='CANCELLED'; REPLACED='REPLACED'; HISTORIC='HISTORIC'

@dataclass(frozen=True,slots=True)
class TitleRecord:
    title_id:str
    parcel_id:str
    title_type_code:str
    tenure_type_code:str
    holder_reference:str
    title_status:TitleStatus|str
    effective_from:date
    effective_to:date|None
    source_reference:str
    runtime_effect_scope:RecordEffectScope|str=RecordEffectScope.RUNTIME_SCOPED
    def __post_init__(self) -> None:
        if not re.fullmatch(r'NG-TTL-\d{6}',self.title_id): raise ValueError('title_id must use governed NG-TTL-###### identity')
        if not re.fullmatch(r'NV-\d{2}-\d{3}-\d{4,}',self.parcel_id): raise ValueError('parcel_id invalid')
        if not self.title_type_code or not self.tenure_type_code: raise ValueError('title and tenure classifications required')
        if not self.holder_reference or any(c.isspace() for c in self.holder_reference): raise ValueError('holder_reference must be an opaque non-whitespace identity reference')
        status=self.title_status if isinstance(self.title_status,TitleStatus) else TitleStatus(str(self.title_status)); object.__setattr__(self,'title_status',status)
        if self.effective_to is not None and self.effective_to < self.effective_from: raise ValueError('effective_to cannot precede effective_from')
        if not self.source_reference: raise ValueError('source_reference required')
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        if scope is not RecordEffectScope.RUNTIME_SCOPED: raise ValueError('title operational effect must remain RUNTIME_SCOPED')
        object.__setattr__(self,'runtime_effect_scope',scope)

class MemoryTitleRepository:
    def __init__(self): self._items:dict[str,TitleRecord]={}
    def add(self,title:TitleRecord):
        p=self._items.get(title.title_id)
        if p is not None and p!=title: raise ValueError('title identifier collision')
        self._items[title.title_id]=title; return title
    def get(self,title_id): return self._items.get(title_id)
    def for_parcel(self,parcel_id): return tuple(sorted((t for t in self._items.values() if t.parcel_id==parcel_id),key=lambda t:t.title_id))
    def all(self): return tuple(self._items[k] for k in sorted(self._items))

__all__=['TitleStatus','TitleRecord','MemoryTitleRepository']
