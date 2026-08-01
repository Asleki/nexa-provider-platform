"""Read-model contracts for scalable Name Authority search."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
import base64,json
from registries.name_authority.authority import AuthorityNameComposition,AuthorityNameStatus,NameAuthorityRecord

@dataclass(frozen=True,slots=True)
class NameAuthorityReadModel:
    authority_name_id:str; runtime_mode:str; composition:AuthorityNameComposition; display_name:str; search_name:str; ordered_component_ids:tuple[str,...]; ordered_component_values:tuple[str,...]; source_strategy:str; status:AuthorityNameStatus; generation_family:str|None=None; generation_batch_id:str|None=None; schema_version:int=1; read_model_version:int=1; projected_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); metadata:Mapping[str,object]=field(default_factory=dict)
    def __post_init__(self):
        if self.runtime_mode not in ("simulation","production"): raise ValueError("runtime_mode is invalid.")
        object.__setattr__(self,"composition",AuthorityNameComposition.parse(self.composition)); object.__setattr__(self,"status",self.status if isinstance(self.status,AuthorityNameStatus) else AuthorityNameStatus(self.status)); object.__setattr__(self,"ordered_component_ids",tuple(self.ordered_component_ids)); object.__setattr__(self,"ordered_component_values",tuple(self.ordered_component_values)); object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))
        if len(self.ordered_component_ids)!=len(self.ordered_component_values): raise ValueError("component IDs and values must align.")

@dataclass(frozen=True,slots=True)
class NameAuthoritySearchCursor:
    runtime_mode:str; search_name:str; authority_name_id:str; read_model_version:int=1
    def encode(self):
        raw=json.dumps({"r":self.runtime_mode,"s":self.search_name,"a":self.authority_name_id,"v":self.read_model_version},separators=(",",":"),ensure_ascii=False).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")
    @classmethod
    def decode(cls,value):
        try:
            raw=base64.urlsafe_b64decode(value+"="*(-len(value)%4)); d=json.loads(raw)
            return cls(d["r"],d["s"],d["a"],int(d["v"]))
        except Exception as exc: raise ValueError("invalid Name Authority search cursor.") from exc

@dataclass(frozen=True,slots=True)
class NameAuthoritySearchQuery:
    runtime_mode:str; text:str=""; exact:bool=False; compositions:tuple[AuthorityNameComposition,...]=(); generation_families:tuple[str,...]=(); statuses:tuple[AuthorityNameStatus,...]=(AuthorityNameStatus.ACTIVE,); generation_batch_id:str|None=None; limit:int=25; cursor:str|None=None
    def __post_init__(self):
        if self.runtime_mode not in ("simulation","production"): raise ValueError("runtime_mode is invalid.")
        if self.limit<1 or self.limit>200: raise ValueError("limit must be between 1 and 200.")
        object.__setattr__(self,"compositions",tuple(AuthorityNameComposition.parse(x) for x in self.compositions)); object.__setattr__(self,"statuses",tuple(x if isinstance(x,AuthorityNameStatus) else AuthorityNameStatus(x) for x in self.statuses))
        if self.cursor and NameAuthoritySearchCursor.decode(self.cursor).runtime_mode!=self.runtime_mode: raise ValueError("cursor runtime does not match query runtime.")

@dataclass(frozen=True,slots=True)
class NameAuthoritySearchResult:
    items:tuple[NameAuthorityReadModel,...]; next_cursor:str|None; has_more:bool; runtime_mode:str; read_model_version:int

@dataclass(frozen=True,slots=True)
class NameAuthorityStatistics:
    runtime_mode:str; total:int; by_composition:Mapping[str,int]; by_generation_family:Mapping[str,int]; by_status:Mapping[str,int]

@dataclass(frozen=True,slots=True)
class ProjectionCheckpoint:
    projection_name:str; runtime_mode:str; last_authority_name_id:str|None; projected_count:int; read_model_version:int; checksum:str; updated_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
