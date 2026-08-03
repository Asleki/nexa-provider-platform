"""Additive production reference-authority contracts for M009.13.10."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
import re, unicodedata

_CODE=re.compile(r"^[a-z]{3}_[0-9]{3,12}$")

def text(v,n):
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{n} is required.")
    return unicodedata.normalize("NFC"," ".join(v.strip().split()))

class ReferenceType(str,Enum):
    TRIBE="tribe"; LANGUAGE="language"; ORIGIN="origin"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())
class ReferenceStatus(str,Enum):
    ACTIVE="active"; SUSPENDED="suspended"; RETIRED="retired"
class OriginType(str,Enum):
    COUNTRY="country"; NATIONALITY_LABEL="nationality_label"; REGIONAL_CULTURE="regional_culture"; HISTORIC_REGION="historic_region"; LINGUISTIC_CULTURE="linguistic_culture"; SOURCE_DECLARED_ORIGIN="source_declared_origin"
class RelationshipState(str,Enum):
    RESOLVED="resolved"; NOT_APPLICABLE="not_applicable"; SOURCE_NOT_PROVIDED="source_not_provided"; QUARANTINED="quarantined"; CONFLICT="conflict"

@dataclass(frozen=True,slots=True)
class ReferenceRecord:
    reference_id:str; reference_code:str; reference_type:ReferenceType|str; canonical_label:str; runtime_mode:str="production"; status:ReferenceStatus|str=ReferenceStatus.ACTIVE; source_reference:str="manual"; origin_type:OriginType|str|None=None; native_label:str|None=None; attributes:Mapping[str,object]=field(default_factory=dict); created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); created_by_actor_id:str="system"; approved_by_actor_id:str="system"
    def __post_init__(self):
        object.__setattr__(self,"reference_id",text(self.reference_id,"reference_id")); object.__setattr__(self,"reference_code",text(self.reference_code,"reference_code").lower())
        if not _CODE.fullmatch(self.reference_code): raise ValueError("reference_code is invalid.")
        object.__setattr__(self,"reference_type",ReferenceType.parse(self.reference_type)); object.__setattr__(self,"canonical_label",text(self.canonical_label,"canonical_label")); object.__setattr__(self,"runtime_mode",text(self.runtime_mode,"runtime_mode").lower())
        object.__setattr__(self,"status",self.status if isinstance(self.status,ReferenceStatus) else ReferenceStatus(str(self.status).lower()))
        object.__setattr__(self,"source_reference",text(self.source_reference,"source_reference")); object.__setattr__(self,"created_by_actor_id",text(self.created_by_actor_id,"created_by_actor_id")); object.__setattr__(self,"approved_by_actor_id",text(self.approved_by_actor_id,"approved_by_actor_id"))
        if self.created_by_actor_id==self.approved_by_actor_id: raise ValueError("submitter and approver must be different actors.")
        if self.origin_type is not None: object.__setattr__(self,"origin_type",self.origin_type if isinstance(self.origin_type,OriginType) else OriginType(str(self.origin_type).lower()))
        if self.native_label is not None: object.__setattr__(self,"native_label",text(self.native_label,"native_label"))
        object.__setattr__(self,"attributes",MappingProxyType(dict(self.attributes)))
    @property
    def search_label(self): return unicodedata.normalize("NFKC",self.canonical_label).casefold()

@dataclass(frozen=True,slots=True)
class ReferenceAuthoringRequest:
    reference_type:ReferenceType|str; canonical_label:str; submitter_actor_id:str; approver_actor_id:str; source_reference:str; runtime_mode:str="production"; origin_type:OriginType|str|None=None; native_label:str|None=None; requested_code:str|None=None; attributes:Mapping[str,object]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"reference_type",ReferenceType.parse(self.reference_type)); object.__setattr__(self,"canonical_label",text(self.canonical_label,"canonical_label")); object.__setattr__(self,"submitter_actor_id",text(self.submitter_actor_id,"submitter_actor_id")); object.__setattr__(self,"approver_actor_id",text(self.approver_actor_id,"approver_actor_id")); object.__setattr__(self,"source_reference",text(self.source_reference,"source_reference")); object.__setattr__(self,"runtime_mode",text(self.runtime_mode,"runtime_mode").lower())
        if self.runtime_mode!="production": raise ValueError("production reference authoring requires production runtime.")
        if self.submitter_actor_id==self.approver_actor_id: raise ValueError("submitter and approver must be different actors.")
        if self.origin_type is not None: object.__setattr__(self,"origin_type",self.origin_type if isinstance(self.origin_type,OriginType) else OriginType(str(self.origin_type).lower()))
        if self.requested_code is not None: object.__setattr__(self,"requested_code",text(self.requested_code,"requested_code").lower())
        object.__setattr__(self,"attributes",MappingProxyType(dict(self.attributes)))

__all__=["ReferenceType","ReferenceStatus","OriginType","RelationshipState","ReferenceRecord","ReferenceAuthoringRequest"]
