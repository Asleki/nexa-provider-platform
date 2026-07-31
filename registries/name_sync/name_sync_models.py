"""Immutable name catalogue snapshot, change, request, and receipt contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from registries.name_cache.name_cache_models import NameCacheEntry

class NameChangeType(str,Enum):
    UPSERT="upsert"; REMOVE="remove"
class NameSyncOperation(str,Enum):
    APPLY_SNAPSHOT="apply_snapshot"; APPLY_CHANGE_SET="apply_change_set"
class NameSyncItemOutcome(str,Enum):
    APPLIED="applied"; SKIPPED="skipped"; REJECTED="rejected"; FAILED="failed"
class NameSyncStatus(str,Enum):
    COMPLETED="completed"; COMPLETED_WITH_FAILURES="completed_with_failures"; REJECTED="rejected"; FAILED="failed"

def text(value,field):
    if not isinstance(value,str): raise TypeError(f"{field} must be text.")
    value=value.strip()
    if not value: raise ValueError(f"{field} cannot be empty.")
    return value

def aware(value,field):
    if not isinstance(value,datetime): raise TypeError(f"{field} must be datetime.")
    if value.tzinfo is None or value.utcoffset() is None: raise ValueError(f"{field} must be timezone-aware.")
    return value

@dataclass(frozen=True,slots=True)
class NameCatalogueSnapshot:
    snapshot_id:str; runtime_mode:str; catalogue_version:str; checkpoint:str; generated_at:datetime; entries:tuple[NameCacheEntry,...]; schema_version:int=1
    def __post_init__(self):
        for f in ("snapshot_id","runtime_mode","catalogue_version","checkpoint"): object.__setattr__(self,f,text(getattr(self,f),f).lower() if f=="runtime_mode" else text(getattr(self,f),f))
        object.__setattr__(self,"generated_at",aware(self.generated_at,"generated_at")); object.__setattr__(self,"entries",tuple(self.entries))
        if self.schema_version<1: raise ValueError("schema_version must be positive.")
        ids=set(); identities=set()
        for e in self.entries:
            if not isinstance(e,NameCacheEntry): raise TypeError("entries must contain NameCacheEntry values.")
            if e.record.metadata.runtime_mode!=self.runtime_mode: raise ValueError("snapshot entry runtime mismatch.")
            if e.record.name_id in ids or e.record.identity_key in identities: raise ValueError("duplicate snapshot entry.")
            ids.add(e.record.name_id); identities.add(e.record.identity_key)

@dataclass(frozen=True,slots=True)
class NameCatalogueChange:
    change_id:str; change_type:NameChangeType; canonical_name_id:str; record_version:str; entry:NameCacheEntry|None=None
    def __post_init__(self):
        for f in ("change_id","canonical_name_id","record_version"): object.__setattr__(self,f,text(getattr(self,f),f))
        if not isinstance(self.change_type,NameChangeType): object.__setattr__(self,"change_type",NameChangeType(self.change_type))
        if self.change_type is NameChangeType.UPSERT and not isinstance(self.entry,NameCacheEntry): raise ValueError("upsert change requires entry.")
        if self.entry is not None and self.entry.record.name_id!=self.canonical_name_id: raise ValueError("change entry identifier mismatch.")
        if self.change_type is NameChangeType.REMOVE and self.entry is not None: raise ValueError("remove change cannot include entry.")

@dataclass(frozen=True,slots=True)
class NameCatalogueChangeSet:
    change_set_id:str; runtime_mode:str; starting_checkpoint:str; ending_checkpoint:str; catalogue_version:str; generated_at:datetime; changes:tuple[NameCatalogueChange,...]; schema_version:int=1
    def __post_init__(self):
        for f in ("change_set_id","runtime_mode","starting_checkpoint","ending_checkpoint","catalogue_version"): object.__setattr__(self,f,text(getattr(self,f),f).lower() if f=="runtime_mode" else text(getattr(self,f),f))
        object.__setattr__(self,"generated_at",aware(self.generated_at,"generated_at")); object.__setattr__(self,"changes",tuple(self.changes))
        if self.schema_version<1: raise ValueError("schema_version must be positive.")
        ids=set()
        for c in self.changes:
            if not isinstance(c,NameCatalogueChange): raise TypeError("changes must contain NameCatalogueChange values.")
            if c.change_id in ids: raise ValueError("duplicate change_id.")
            ids.add(c.change_id)
            if c.entry is not None and c.entry.record.metadata.runtime_mode!=self.runtime_mode: raise ValueError("change entry runtime mismatch.")

@dataclass(frozen=True,slots=True)
class NameSyncRequest:
    request_id:str; operation:NameSyncOperation; runtime_mode:str; requested_at:datetime; client_id:str|None=None
    def __post_init__(self):
        object.__setattr__(self,"request_id",text(self.request_id,"request_id")); object.__setattr__(self,"runtime_mode",text(self.runtime_mode,"runtime_mode").lower()); object.__setattr__(self,"requested_at",aware(self.requested_at,"requested_at"))
        if not isinstance(self.operation,NameSyncOperation): object.__setattr__(self,"operation",NameSyncOperation(self.operation))
        if self.client_id is not None: object.__setattr__(self,"client_id",text(self.client_id,"client_id"))

@dataclass(frozen=True,slots=True)
class NameSyncItemResult:
    item_id:str; outcome:NameSyncItemOutcome; canonical_name_id:str|None=None; message:str=""
    def __post_init__(self):
        object.__setattr__(self,"item_id",text(self.item_id,"item_id"))
        if not isinstance(self.outcome,NameSyncItemOutcome): object.__setattr__(self,"outcome",NameSyncItemOutcome(self.outcome))
        if self.canonical_name_id is not None: object.__setattr__(self,"canonical_name_id",text(self.canonical_name_id,"canonical_name_id"))
        if not isinstance(self.message,str): raise TypeError("message must be text.")

@dataclass(frozen=True,slots=True)
class NameSyncReceipt:
    receipt_id:str; request_id:str; runtime_mode:str; status:NameSyncStatus; processed_at:datetime; starting_checkpoint:str|None; ending_checkpoint:str|None; items:tuple[NameSyncItemResult,...]
    def __post_init__(self):
        for f in ("receipt_id","request_id","runtime_mode"): object.__setattr__(self,f,text(getattr(self,f),f).lower() if f=="runtime_mode" else text(getattr(self,f),f))
        if not isinstance(self.status,NameSyncStatus): object.__setattr__(self,"status",NameSyncStatus(self.status))
        object.__setattr__(self,"processed_at",aware(self.processed_at,"processed_at")); object.__setattr__(self,"items",tuple(self.items))
        for f in ("starting_checkpoint","ending_checkpoint"):
            if getattr(self,f) is not None: object.__setattr__(self,f,text(getattr(self,f),f))
    @property
    def accepted_count(self): return sum(i.outcome is NameSyncItemOutcome.APPLIED for i in self.items)
    @property
    def skipped_count(self): return sum(i.outcome is NameSyncItemOutcome.SKIPPED for i in self.items)
    @property
    def rejected_count(self): return sum(i.outcome is NameSyncItemOutcome.REJECTED for i in self.items)
    @property
    def failed_count(self): return sum(i.outcome is NameSyncItemOutcome.FAILED for i in self.items)
