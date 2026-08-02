"""Migration ledger contracts and deterministic memory implementation."""
from __future__ import annotations
from dataclasses import dataclass,replace
from datetime import datetime,timezone
from typing import Protocol
from .constants import LEDGER_STATUSES,SHA256_HEX_LENGTH
from .errors import MigrationLedgerError
@dataclass(frozen=True,slots=True)
class MigrationLedgerRecord:
    migration_id:str; milestone_id:str; filename:str; sequence_number:int; checksum_sha256:str; status:str; execution_id:str; started_at:datetime
    completed_at:datetime|None=None; execution_duration_ms:int|None=None; applied_by:str="unknown"; database_name:str=""; environment_name:str=""; runner_version:str=""; repository_revision:str="unknown"; error_code:str|None=None; error_summary:str|None=None
    def __post_init__(self):
        if self.status not in LEDGER_STATUSES: raise MigrationLedgerError("unsupported ledger status.")
        if len(self.checksum_sha256)!=SHA256_HEX_LENGTH or any(c not in '0123456789abcdef' for c in self.checksum_sha256.lower()): raise MigrationLedgerError("ledger checksum must be SHA-256.")
        if self.sequence_number<1: raise MigrationLedgerError("sequence_number must be positive.")
        for secret in ('password=','postgresql://','postgres://'):
            if secret in ((self.error_summary or '').lower()): raise MigrationLedgerError("ledger content contains prohibited secret material.")
class MigrationLedger(Protocol):
    def is_bootstrapped(self)->bool: ...
    def history(self)->tuple[MigrationLedgerRecord,...]: ...
    def get(self,migration_id:str)->MigrationLedgerRecord|None: ...
    def insert_started(self,record:MigrationLedgerRecord)->None: ...
    def mark_applied(self,migration_id:str,*,completed_at:datetime,duration_ms:int)->None: ...
    def mark_failed(self,migration_id:str,*,completed_at:datetime,duration_ms:int,error_code:str,error_summary:str)->None: ...
class MemoryMigrationLedger:
    def __init__(self,bootstrapped:bool=True): self._bootstrapped=bootstrapped; self._records={}
    def bootstrap(self): self._bootstrapped=True
    def is_bootstrapped(self): return self._bootstrapped
    def history(self): return tuple(sorted(self._records.values(),key=lambda r:(r.sequence_number,r.migration_id)))
    def get(self,migration_id): return self._records.get(migration_id)
    def insert_started(self,record):
        if record.migration_id in self._records: raise MigrationLedgerError("migration already exists in ledger.")
        if record.status!='STARTED': raise MigrationLedgerError("new ledger record must be STARTED.")
        self._records[record.migration_id]=record
    def mark_applied(self,migration_id,*,completed_at,duration_ms): self._transition(migration_id,'APPLIED',completed_at,duration_ms,None,None)
    def mark_failed(self,migration_id,*,completed_at,duration_ms,error_code,error_summary): self._transition(migration_id,'FAILED',completed_at,duration_ms,error_code,error_summary)
    def _transition(self,migration_id,status,completed_at,duration_ms,error_code,error_summary):
        current=self._records.get(migration_id)
        if current is None: raise MigrationLedgerError("migration ledger record does not exist.")
        if current.status!='STARTED': raise MigrationLedgerError("only STARTED records may transition.")
        self._records[migration_id]=replace(current,status=status,completed_at=completed_at,execution_duration_ms=duration_ms,error_code=error_code,error_summary=error_summary)
