"""Immutable result page for name catalogue search."""
from __future__ import annotations
from dataclasses import dataclass
from .canonical_name import CanonicalName
@dataclass(frozen=True,slots=True)
class NameSearchResult:
    records: tuple[CanonicalName,...]
    total: int
    limit: int
    offset: int
    def __post_init__(self)->None:
        object.__setattr__(self,"records",tuple(self.records))
        if any(not isinstance(r,CanonicalName) for r in self.records): raise TypeError("records must contain CanonicalName values.")
        for n in ("total","limit","offset"):
            v=getattr(self,n)
            if isinstance(v,bool) or not isinstance(v,int): raise TypeError(f"{n} must be an integer.")
        if self.total<0 or self.offset<0 or self.limit<1: raise ValueError("invalid pagination values.")
        if len(self.records)>self.limit or self.offset>self.total: raise ValueError("inconsistent search result pagination.")
__all__=["NameSearchResult"]
