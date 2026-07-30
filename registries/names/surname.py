"""Surname catalogue record."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from .canonical_name import CanonicalName
from .name_kind import NameKind
from .name_metadata import NameMetadata
@dataclass(frozen=True,slots=True)
class Surname:
    name_id: str
    canonical_value: str
    metadata: NameMetadata=field(default_factory=NameMetadata)
    def as_canonical(self)->CanonicalName: return CanonicalName(self.name_id,self.canonical_value,NameKind.SURNAME,self.metadata)
    def __post_init__(self)->None:
        c=self.as_canonical(); object.__setattr__(self,"name_id",c.name_id); object.__setattr__(self,"canonical_value",c.canonical_value)
    @property
    def name_kind(self)->NameKind: return NameKind.SURNAME
    @property
    def search_value(self)->str: return self.as_canonical().search_value
    def to_dict(self)->dict[str,object]: return self.as_canonical().to_dict()
    @classmethod
    def from_dict(cls,data:Mapping[str,object])->"Surname":
        c=CanonicalName.from_dict(data)
        if c.name_kind is not NameKind.SURNAME: raise ValueError("name_kind must be surname.")
        return cls(c.name_id,c.canonical_value,c.metadata)
__all__=["Surname"]
