"""Name orthography and semantic context contracts for M009.13.10."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
import unicodedata,re

class NameStructureType(str,Enum):
    SIMPLE="simple"; COMPOUND_SPACE_SEPARATED="compound_space_separated"; HYPHENATED="hyphenated"; APOSTROPHIZED="apostrophized"; PREFIXED_COMPOUND="prefixed_compound"; JOINED_PREFIX="joined_prefix"; MULTI_SURNAME="multi_surname"; MIXED_FORM="mixed_form"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())
class NameContextRole(str,Enum):
    NATIVE_SURNAME_TRIBE="native_surname_tribe"; SURNAME_ORIGIN="surname_origin"; SURNAME_LANGUAGE="surname_language"; FIRST_NAME_LANGUAGE="first_name_language"; MIDDLE_NAME_LANGUAGE="middle_name_language"; NOT_APPLICABLE_TRIBE="not_applicable_tribe"; NOT_APPLICABLE_ORIGIN="not_applicable_origin"
class ContextState(str,Enum):
    RESOLVED="resolved"; NOT_APPLICABLE="not_applicable"; SOURCE_NOT_PROVIDED="source_not_provided"; QUARANTINED="quarantined"; CONFLICT="conflict"

def req(v,n):
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{n} is required.")
    return v.strip()

def tokenize(value): return tuple(re.findall(r"[^\s\-']+",value,flags=re.UNICODE))
def separators(value): return tuple(ch for ch in value if ch.isspace() or ch in "-'’")

@dataclass(frozen=True,slots=True)
class NameOrthographyProfile:
    profile_id:str; name_id:str; runtime_mode:str; structure_type:NameStructureType|str; canonical_value_snapshot:str; created_by_actor_id:str; approved_by_actor_id:str; accented:bool|None=None; accent_stripping_authorized:bool=False; tokens:tuple[str,...]=(); separators:tuple[str,...]=(); source_reference:str="manual"; attributes:Mapping[str,object]=field(default_factory=dict); created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    def __post_init__(self):
        for n in ("profile_id","name_id","runtime_mode","canonical_value_snapshot","created_by_actor_id","approved_by_actor_id","source_reference"): object.__setattr__(self,n,req(getattr(self,n),n))
        object.__setattr__(self,"structure_type",NameStructureType.parse(self.structure_type))
        if self.created_by_actor_id==self.approved_by_actor_id: raise ValueError("submitter and approver must be different actors.")
        canonical=unicodedata.normalize("NFC",self.canonical_value_snapshot); object.__setattr__(self,"canonical_value_snapshot",canonical)
        detected=any(ord(c)>127 for c in canonical)
        if self.accented is None: object.__setattr__(self,"accented",detected)
        if self.accent_stripping_authorized: raise ValueError("accent stripping is not authorized in M009.13.10.")
        ts=tuple(self.tokens) or tokenize(canonical); ss=tuple(self.separators) or separators(canonical); object.__setattr__(self,"tokens",ts); object.__setattr__(self,"separators",ss); object.__setattr__(self,"attributes",MappingProxyType(dict(self.attributes)))
        self._validate()
    def _validate(self):
        s=self.structure_type; v=self.canonical_value_snapshot
        if s is NameStructureType.SIMPLE and (len(self.tokens)!=1 or any(x in v for x in ("-","'","’"))): raise ValueError("simple names must have one token and no structural punctuation.")
        if s is NameStructureType.COMPOUND_SPACE_SEPARATED and len(v.split())<2: raise ValueError("compound_space_separated requires at least two tokens.")
        if s is NameStructureType.HYPHENATED and "-" not in v: raise ValueError("hyphenated requires a hyphen.")
        if s is NameStructureType.APOSTROPHIZED and "'" not in v and "’" not in v: raise ValueError("apostrophized requires an apostrophe.")
        if s is NameStructureType.PREFIXED_COMPOUND and len(v.split())<2: raise ValueError("prefixed_compound requires multiple tokens.")
    @property
    def token_count(self): return len(self.tokens)

@dataclass(frozen=True,slots=True)
class NameContextRelationship:
    relationship_id:str; name_id:str; runtime_mode:str; role:NameContextRole|str; state:ContextState|str; created_by_actor_id:str; approved_by_actor_id:str; target_reference_id:str|None=None; source_reference:str="manual"; attributes:Mapping[str,object]=field(default_factory=dict); created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    def __post_init__(self):
        for n in ("relationship_id","name_id","runtime_mode","created_by_actor_id","approved_by_actor_id","source_reference"): object.__setattr__(self,n,req(getattr(self,n),n))
        object.__setattr__(self,"role",self.role if isinstance(self.role,NameContextRole) else NameContextRole(str(self.role).lower())); object.__setattr__(self,"state",self.state if isinstance(self.state,ContextState) else ContextState(str(self.state).lower()))
        if self.created_by_actor_id==self.approved_by_actor_id: raise ValueError("submitter and approver must be different actors.")
        if self.state is ContextState.RESOLVED and not self.target_reference_id: raise ValueError("resolved relationships require target_reference_id.")
        if self.state is ContextState.NOT_APPLICABLE and self.target_reference_id is not None: raise ValueError("not-applicable relationships cannot target a reference.")
        object.__setattr__(self,"attributes",MappingProxyType(dict(self.attributes)))

@dataclass(frozen=True,slots=True)
class NameProductionContextRequest:
    name_id:str; runtime_mode:str; name_kind:str; classification:str; structure_type:NameStructureType|str; canonical_value:str; submitter_actor_id:str; approver_actor_id:str; language_reference_id:str|None=None; origin_reference_id:str|None=None; tribe_reference_id:str|None=None; source_reference:str="manual"
    def __post_init__(self):
        for n in ("name_id","runtime_mode","name_kind","classification","canonical_value","submitter_actor_id","approver_actor_id","source_reference"): object.__setattr__(self,n,req(getattr(self,n),n))
        object.__setattr__(self,"structure_type",NameStructureType.parse(self.structure_type)); object.__setattr__(self,"classification",self.classification.lower()); object.__setattr__(self,"name_kind",self.name_kind.lower()); object.__setattr__(self,"runtime_mode",self.runtime_mode.lower())
        if self.submitter_actor_id==self.approver_actor_id: raise ValueError("submitter and approver must be different actors.")

__all__=["NameStructureType","NameContextRole","ContextState","NameOrthographyProfile","NameContextRelationship","NameProductionContextRequest"]
