from dataclasses import dataclass
from enum import Enum
class NameImportOutcome(str,Enum): IMPORTED="imported"; ALREADY_EXISTS="already_exists"; SKIPPED="skipped"; FAILED="failed"
@dataclass(frozen=True,slots=True)
class NameImportItemResult:
    candidate_id:str; outcome:NameImportOutcome; canonical_name_id:str|None=None; message:str|None=None
    def __post_init__(self):
        object.__setattr__(self,"outcome",NameImportOutcome(self.outcome))
@dataclass(frozen=True,slots=True)
class NameImportBatchResult:
    batch_id:str; items:tuple[NameImportItemResult,...]
    @property
    def imported_count(self): return sum(i.outcome is NameImportOutcome.IMPORTED for i in self.items)
    @property
    def existing_count(self): return sum(i.outcome is NameImportOutcome.ALREADY_EXISTS for i in self.items)
    @property
    def failed_count(self): return sum(i.outcome is NameImportOutcome.FAILED for i in self.items)
    @property
    def complete(self): return self.failed_count==0
__all__=["NameImportOutcome","NameImportItemResult","NameImportBatchResult"]
