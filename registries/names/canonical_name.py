"""Immutable canonical name record for M009.1."""
from __future__ import annotations
import re, unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final
from .name_kind import NameKind
from .name_metadata import NameMetadata

_ID: Final[re.Pattern[str]]=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_MAX_VALUE: Final[int]=200

def normalize_name_value(value: object)->str:
    if not isinstance(value,str): raise TypeError("canonical_value must be text.")
    value=unicodedata.normalize("NFC"," ".join(value.strip().split()))
    if not value: raise ValueError("canonical_value cannot be empty.")
    if len(value)>_MAX_VALUE: raise ValueError(f"canonical_value cannot exceed {_MAX_VALUE} characters.")
    if any(unicodedata.category(ch).startswith("C") for ch in value): raise ValueError("canonical_value cannot contain control characters.")
    return value

def comparison_key(value: str)->str:
    return unicodedata.normalize("NFKC",value).casefold()

@dataclass(frozen=True,slots=True)
class CanonicalName:
    name_id: str
    canonical_value: str
    name_kind: NameKind
    metadata: NameMetadata=field(default_factory=NameMetadata)

    def __post_init__(self)->None:
        if not isinstance(self.name_id,str): raise TypeError("name_id must be text.")
        ident=self.name_id.strip()
        if not _ID.fullmatch(ident): raise ValueError("name_id is invalid.")
        object.__setattr__(self,"name_id",ident)
        value=normalize_name_value(self.canonical_value)
        object.__setattr__(self,"canonical_value",value)
        object.__setattr__(self,"name_kind",NameKind.parse(self.name_kind))
        if not isinstance(self.metadata,NameMetadata): raise TypeError("metadata must be NameMetadata.")

    @property
    def search_value(self)->str: return comparison_key(self.canonical_value)
    @property
    def identity_key(self)->tuple[str,str,str]: return (self.metadata.runtime_mode,self.name_kind.value,self.search_value)
    def to_dict(self)->dict[str,object]: return {"name_id":self.name_id,"canonical_value":self.canonical_value,"name_kind":self.name_kind.value,"search_value":self.search_value,"metadata":self.metadata.to_dict()}
    @classmethod
    def from_dict(cls,data: Mapping[str,object])->"CanonicalName":
        if not isinstance(data,Mapping): raise TypeError("data must be a mapping.")
        allowed={"name_id","canonical_value","name_kind","search_value","metadata"}
        unknown=set(data)-allowed
        if unknown: raise ValueError(f"unknown canonical name fields: {', '.join(sorted(map(str,unknown)))}.")
        values=dict(data); values.pop("search_value",None)
        md=values.get("metadata")
        if isinstance(md,Mapping): values["metadata"]=NameMetadata.from_dict(md)
        return cls(**values)

__all__=["CanonicalName","comparison_key","normalize_name_value"]
