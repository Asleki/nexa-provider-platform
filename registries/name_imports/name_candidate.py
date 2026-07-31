"""Immutable local name candidate, distinct from a canonical name."""
from __future__ import annotations
import re
from collections.abc import Mapping
from dataclasses import dataclass,field
from datetime import datetime,timezone
from types import MappingProxyType
from registries.names.name_kind import NameKind
from registries.names.name_sex_usage import NameSexUsage
from .name_candidate_status import NameCandidateStatus
_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_RUNTIME=re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
def _ident(value:object,name:str)->str:
    if not isinstance(value,str): raise TypeError(f"{name} must be text.")
    value=value.strip()
    if not _ID.fullmatch(value): raise ValueError(f"{name} is invalid.")
    return value
def _utc(value:object)->datetime:
    if not isinstance(value,datetime): raise TypeError("created_at must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None: raise ValueError("created_at must be timezone-aware.")
    return value.astimezone(timezone.utc)
def _refs(value:object,name:str)->tuple[str,...]:
    if value is None:return ()
    if isinstance(value,str): value=tuple(x.strip() for x in value.split("|") if x.strip())
    if not isinstance(value,(tuple,list,set,frozenset)): raise TypeError(f"{name} must be an iterable of references.")
    return tuple(dict.fromkeys(_ident(v,name) for v in value))
@dataclass(frozen=True,slots=True)
class NameCandidate:
    candidate_id:str; batch_id:str; source_id:str; source_row_number:int; raw_name_value:str; name_kind:NameKind; runtime_mode:str
    sex_usage:NameSexUsage=NameSexUsage.UNSPECIFIED; source_reference:str|None=None; external_record_id:str|None=None
    language_refs:tuple[str,...]=(); country_refs:tuple[str,...]=(); region_refs:tuple[str,...]=(); culture_refs:tuple[str,...]=(); script_code:str|None=None
    attributes:Mapping[str,object]=field(default_factory=dict); status:NameCandidateStatus=NameCandidateStatus.STAGED; schema_version:int=1
    created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    def __post_init__(self)->None:
        for n in ("candidate_id","batch_id","source_id"): object.__setattr__(self,n,_ident(getattr(self,n),n))
        if isinstance(self.source_row_number,bool) or not isinstance(self.source_row_number,int): raise TypeError("source_row_number must be an integer.")
        if self.source_row_number<2: raise ValueError("source_row_number must be at least 2.")
        if not isinstance(self.raw_name_value,str): raise TypeError("raw_name_value must be text.")
        object.__setattr__(self,"raw_name_value",self.raw_name_value.strip())
        object.__setattr__(self,"name_kind",NameKind.parse(self.name_kind)); object.__setattr__(self,"sex_usage",NameSexUsage.parse(self.sex_usage)); object.__setattr__(self,"status",NameCandidateStatus.parse(self.status))
        if not isinstance(self.runtime_mode,str): raise TypeError("runtime_mode must be text.")
        runtime=self.runtime_mode.strip().lower()
        if not _RUNTIME.fullmatch(runtime): raise ValueError("runtime_mode is invalid.")
        object.__setattr__(self,"runtime_mode",runtime)
        for n in ("source_reference","external_record_id"):
            value=getattr(self,n)
            if value is not None: object.__setattr__(self,n,_ident(value,n))
        for n in ("language_refs","country_refs","region_refs","culture_refs"): object.__setattr__(self,n,_refs(getattr(self,n),n))
        if self.script_code is not None:
            if not isinstance(self.script_code,str): raise TypeError("script_code must be text or None.")
            code=self.script_code.strip()
            if not code or len(code)>32: raise ValueError("script_code must contain 1-32 characters.")
            object.__setattr__(self,"script_code",code)
        if not isinstance(self.attributes,Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self,"attributes",MappingProxyType(dict(self.attributes)))
        if isinstance(self.schema_version,bool) or not isinstance(self.schema_version,int): raise TypeError("schema_version must be an integer.")
        if self.schema_version<1: raise ValueError("schema_version must be at least 1.")
        object.__setattr__(self,"created_at",_utc(self.created_at))
    def with_status(self,status:NameCandidateStatus|str)->"NameCandidate":
        data={f:getattr(self,f) for f in self.__dataclass_fields__}; data["status"]=status; return NameCandidate(**data)
__all__=["NameCandidate"]
