"""Immutable metadata shared by canonical name records.

References remain opaque so later language, geography, culture and source registries can
link without being embedded in this contract.
"""
from __future__ import annotations
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Final
from .name_status import NameStatus

_REF: Final[re.Pattern[str]]=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_RUNTIME: Final[re.Pattern[str]]=re.compile(r"^[a-z][a-z0-9_-]{0,63}$")

def _utc(v: object, field_name: str)->datetime:
    if not isinstance(v, datetime): raise TypeError(f"{field_name} must be a datetime.")
    if v.tzinfo is None or v.utcoffset() is None: raise ValueError(f"{field_name} must be timezone-aware.")
    return v.astimezone(timezone.utc)

def _freeze(v: object)->object:
    if isinstance(v, Mapping):
        d={}
        for k,n in v.items():
            if not isinstance(k,str): raise TypeError("attribute keys must be text.")
            key=k.strip()
            if not key: raise ValueError("attribute keys cannot be empty.")
            if key in d: raise ValueError("attribute keys must remain unique after trimming.")
            d[key]=_freeze(n)
        return MappingProxyType(d)
    if isinstance(v,(list,tuple)): return tuple(_freeze(x) for x in v)
    if isinstance(v,(set,frozenset)): return frozenset(_freeze(x) for x in v)
    return v

def _thaw(v: object)->object:
    if isinstance(v,Mapping): return {k:_thaw(n) for k,n in v.items()}
    if isinstance(v,tuple): return [_thaw(x) for x in v]
    if isinstance(v,frozenset): return [_thaw(x) for x in sorted(v,key=repr)]
    return v

def _refs(value: object, name: str)->tuple[str,...]:
    if value is None: return ()
    if isinstance(value,str) or not isinstance(value,(tuple,list,set,frozenset)): raise TypeError(f"{name} must be an iterable of text references.")
    out=[]
    for raw in value:
        if not isinstance(raw,str): raise TypeError(f"{name} entries must be text.")
        item=raw.strip()
        if not _REF.fullmatch(item): raise ValueError(f"invalid {name} reference: {raw!r}.")
        if item not in out: out.append(item)
    return tuple(out)

@dataclass(frozen=True,slots=True)
class NameMetadata:
    status: NameStatus=NameStatus.ACTIVE
    runtime_mode: str="simulation"
    schema_version: int=1
    created_at: datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    source_reference: str|None=None
    language_refs: tuple[str,...]=()
    country_refs: tuple[str,...]=()
    region_refs: tuple[str,...]=()
    culture_refs: tuple[str,...]=()
    script_code: str|None=None
    attributes: Mapping[str,object]=field(default_factory=dict)

    def __post_init__(self)->None:
        object.__setattr__(self,"status",NameStatus.parse(self.status))
        if not isinstance(self.runtime_mode,str): raise TypeError("runtime_mode must be text.")
        runtime=self.runtime_mode.strip().lower()
        if not _RUNTIME.fullmatch(runtime): raise ValueError("runtime_mode is invalid.")
        object.__setattr__(self,"runtime_mode",runtime)
        if isinstance(self.schema_version,bool) or not isinstance(self.schema_version,int): raise TypeError("schema_version must be an integer.")
        if self.schema_version<1: raise ValueError("schema_version must be at least 1.")
        object.__setattr__(self,"created_at",_utc(self.created_at,"created_at"))
        if self.source_reference is not None:
            if not isinstance(self.source_reference,str): raise TypeError("source_reference must be text or None.")
            ref=self.source_reference.strip()
            if not _REF.fullmatch(ref): raise ValueError("source_reference is invalid.")
            object.__setattr__(self,"source_reference",ref)
        for n in ("language_refs","country_refs","region_refs","culture_refs"):
            object.__setattr__(self,n,_refs(getattr(self,n),n))
        if self.script_code is not None:
            if not isinstance(self.script_code,str): raise TypeError("script_code must be text or None.")
            code=self.script_code.strip()
            if not code or len(code)>32: raise ValueError("script_code must contain 1-32 characters.")
            object.__setattr__(self,"script_code",code)
        if not isinstance(self.attributes,Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self,"attributes",_freeze(self.attributes))

    def to_dict(self)->dict[str,object]:
        return {"status":self.status.value,"runtime_mode":self.runtime_mode,"schema_version":self.schema_version,"created_at":self.created_at.isoformat(),"source_reference":self.source_reference,"language_refs":list(self.language_refs),"country_refs":list(self.country_refs),"region_refs":list(self.region_refs),"culture_refs":list(self.culture_refs),"script_code":self.script_code,"attributes":_thaw(self.attributes)}

    @classmethod
    def from_dict(cls,data: Mapping[str,object])->"NameMetadata":
        if not isinstance(data,Mapping): raise TypeError("data must be a mapping.")
        values=dict(data)
        if "created_at" in values and isinstance(values["created_at"],str): values["created_at"]=datetime.fromisoformat(values["created_at"].replace("Z","+00:00"))
        return cls(**values)

__all__=["NameMetadata"]
