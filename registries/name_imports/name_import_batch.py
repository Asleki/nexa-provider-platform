from __future__ import annotations
import re
from dataclasses import dataclass,field
from datetime import datetime,timezone
from .name_candidate import NameCandidate
from .name_candidate_status import NameCandidateStatus
_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"); _RUN=re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
@dataclass(frozen=True,slots=True)
class NameImportBatch:
    batch_id:str; runtime_mode:str; source_id:str; source_name:str; candidates:tuple[NameCandidate,...]=(); approved:bool=False; created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); source_checksum:str|None=None
    def __post_init__(self)->None:
        for n in ("batch_id","source_id"):
            v=getattr(self,n)
            if not isinstance(v,str) or not _ID.fullmatch(v.strip()): raise ValueError(f"{n} is invalid.")
            object.__setattr__(self,n,v.strip())
        if not isinstance(self.runtime_mode,str): raise TypeError("runtime_mode must be text.")
        r=self.runtime_mode.strip().lower()
        if not _RUN.fullmatch(r): raise ValueError("runtime_mode is invalid.")
        object.__setattr__(self,"runtime_mode",r)
        if not isinstance(self.source_name,str) or not self.source_name.strip(): raise ValueError("source_name cannot be empty.")
        object.__setattr__(self,"source_name",self.source_name.strip())
        cs=tuple(self.candidates)
        if not all(isinstance(c,NameCandidate) for c in cs): raise TypeError("candidates must contain NameCandidate values.")
        if len({c.candidate_id for c in cs})!=len(cs): raise ValueError("candidate IDs must be unique within a batch.")
        if any(c.batch_id!=self.batch_id or c.runtime_mode!=r or c.source_id!=self.source_id for c in cs): raise ValueError("candidate batch, runtime, and source references must match the batch.")
        object.__setattr__(self,"candidates",cs)
        if not isinstance(self.approved,bool): raise TypeError("approved must be a boolean.")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None: raise ValueError("created_at must be timezone-aware.")
        object.__setattr__(self,"created_at",self.created_at.astimezone(timezone.utc))
    def approve(self)->"NameImportBatch":
        allowed={NameCandidateStatus.VALIDATED,NameCandidateStatus.APPROVED}
        if any(c.status not in allowed for c in self.candidates): raise ValueError("only fully validated batches can be approved.")
        return NameImportBatch(self.batch_id,self.runtime_mode,self.source_id,self.source_name,tuple(c.with_status(NameCandidateStatus.APPROVED) for c in self.candidates),True,self.created_at,self.source_checksum)
__all__=["NameImportBatch"]
