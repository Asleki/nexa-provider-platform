"""Immutable deterministic query for name catalogue search."""
from __future__ import annotations
from dataclasses import dataclass
from .name_kind import NameKind
from .name_status import NameStatus
@dataclass(frozen=True,slots=True)
class NameSearchQuery:
    text: str=""
    name_kind: NameKind|None=None
    status: NameStatus|None=NameStatus.ACTIVE
    runtime_mode: str|None=None
    exact: bool=False
    limit: int=50
    offset: int=0
    def __post_init__(self)->None:
        if not isinstance(self.text,str): raise TypeError("text must be text.")
        object.__setattr__(self,"text"," ".join(self.text.strip().split()))
        if self.name_kind is not None: object.__setattr__(self,"name_kind",NameKind.parse(self.name_kind))
        if self.status is not None: object.__setattr__(self,"status",NameStatus.parse(self.status))
        if self.runtime_mode is not None:
            if not isinstance(self.runtime_mode,str): raise TypeError("runtime_mode must be text or None.")
            runtime=self.runtime_mode.strip().lower()
            if not runtime: raise ValueError("runtime_mode cannot be empty.")
            object.__setattr__(self,"runtime_mode",runtime)
        for n in ("limit","offset"):
            v=getattr(self,n)
            if isinstance(v,bool) or not isinstance(v,int): raise TypeError(f"{n} must be an integer.")
        if not 1<=self.limit<=1000: raise ValueError("limit must be between 1 and 1000.")
        if self.offset<0: raise ValueError("offset cannot be negative.")
__all__=["NameSearchQuery"]
