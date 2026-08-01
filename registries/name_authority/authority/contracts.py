"""Flexible full-name authority contracts."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
import hashlib,re
from registries.names import NameKind,NameStatus,comparison_key
_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
class AuthorityNameComposition(str,Enum):
    SINGLE_NAME="single_name"; FIRST_SURNAME="first_surname"; FIRST_MIDDLE="first_middle"; FIRST_MIDDLE_SURNAME="first_middle_surname"; INTERNATIONAL_PAIR="international_pair"; COMPOUND_SURNAME="compound_surname"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())
class AuthorityComponentRole(str,Enum):
    SINGLE_NAME="single_name"; FIRST_NAME="first_name"; MIDDLE_NAME="middle_name"; SURNAME="surname"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())
class AuthorityNameStatus(str,Enum): ACTIVE="active"; SUSPENDED="suspended"; RETIRED="retired"; SUPERSEDED="superseded"
@dataclass(frozen=True,slots=True)
class AuthorityNameComponent:
    position:int; name_id:str; name_kind:NameKind; role:AuthorityComponentRole; canonical_value:str; separator_after:str=" "
    def __post_init__(self):
        if self.position<1 or not _ID.fullmatch(self.name_id): raise ValueError("authority component identity is invalid.")
        object.__setattr__(self,"name_kind",NameKind.parse(self.name_kind)); object.__setattr__(self,"role",AuthorityComponentRole.parse(self.role))
@dataclass(frozen=True,slots=True)
class NameAuthorityRecord:
    authority_name_id:str; runtime_mode:str; composition:AuthorityNameComposition; components:tuple[AuthorityNameComponent,...]
    display_name:str; search_name:str; composition_key:str; source_strategy:str="human_production"; status:AuthorityNameStatus=AuthorityNameStatus.ACTIVE
    schema_version:int=1; created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); created_by_actor_id:str="system"; approved_at:datetime|None=None; approved_by_actor_id:str|None=None; supersedes_authority_name_id:str|None=None; metadata:Mapping[str,object]=field(default_factory=dict)
    def __post_init__(self):
        if not _ID.fullmatch(self.authority_name_id): raise ValueError("authority_name_id is invalid.")
        if self.runtime_mode not in ("production","simulation"): raise ValueError("runtime_mode is invalid.")
        object.__setattr__(self,"composition",AuthorityNameComposition.parse(self.composition)); object.__setattr__(self,"components",tuple(self.components)); object.__setattr__(self,"status",self.status if isinstance(self.status,AuthorityNameStatus) else AuthorityNameStatus(self.status)); object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))
        if not self.components or [c.position for c in self.components]!=list(range(1,len(self.components)+1)): raise ValueError("authority components must be contiguous and ordered.")
