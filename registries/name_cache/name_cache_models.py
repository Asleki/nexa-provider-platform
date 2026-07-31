"""Immutable offline name catalogue cache models for M009.10.9."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from registries.names.canonical_name import CanonicalName

class NameCacheStatus(str, Enum):
    EMPTY="empty"; READY="ready"; STALE="stale"; DEGRADED="degraded"; BLOCKED_SCHEMA="blocked_schema"; FAILED="failed"
    @classmethod
    def parse(cls, value: object) -> "NameCacheStatus":
        if isinstance(value, cls): return value
        if not isinstance(value, str): raise TypeError("cache status must be text.")
        try: return cls(value.strip().lower())
        except ValueError as exc: raise ValueError("unsupported cache status.") from exc

def _text(value: object, field: str) -> str:
    if not isinstance(value, str): raise TypeError(f"{field} must be text.")
    value=value.strip()
    if not value: raise ValueError(f"{field} cannot be empty.")
    return value

def _aware(value: object, field: str) -> datetime:
    if not isinstance(value, datetime): raise TypeError(f"{field} must be datetime.")
    if value.tzinfo is None or value.utcoffset() is None: raise ValueError(f"{field} must be timezone-aware.")
    return value

@dataclass(frozen=True, slots=True)
class NameCacheEntry:
    record: CanonicalName
    record_version: str
    cached_at: datetime
    def __post_init__(self):
        if not isinstance(self.record, CanonicalName): raise TypeError("record must be CanonicalName.")
        object.__setattr__(self,"record_version",_text(self.record_version,"record_version"))
        object.__setattr__(self,"cached_at",_aware(self.cached_at,"cached_at"))

@dataclass(frozen=True, slots=True)
class NameCacheState:
    runtime_mode: str
    status: NameCacheStatus=NameCacheStatus.EMPTY
    schema_version: int=1
    catalogue_version: str|None=None
    checkpoint: str|None=None
    entry_count: int=0
    last_synced_at: datetime|None=None
    def __post_init__(self):
        object.__setattr__(self,"runtime_mode",_text(self.runtime_mode,"runtime_mode").lower())
        object.__setattr__(self,"status",NameCacheStatus.parse(self.status))
        if isinstance(self.schema_version,bool) or not isinstance(self.schema_version,int): raise TypeError("schema_version must be integer.")
        if self.schema_version < 1: raise ValueError("schema_version must be positive.")
        if isinstance(self.entry_count,bool) or not isinstance(self.entry_count,int): raise TypeError("entry_count must be integer.")
        if self.entry_count < 0: raise ValueError("entry_count cannot be negative.")
        for field in ("catalogue_version","checkpoint"):
            value=getattr(self,field)
            if value is not None: object.__setattr__(self,field,_text(value,field))
        if self.last_synced_at is not None: object.__setattr__(self,"last_synced_at",_aware(self.last_synced_at,"last_synced_at"))
