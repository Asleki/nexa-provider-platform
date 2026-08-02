"""Narrow migration-ledger bootstrap orchestration."""
from __future__ import annotations
from pathlib import Path
from .errors import MigrationBootstrapError
class MigrationBootstrapService:
    def __init__(self,adapter,sql_root:Path): self.adapter=adapter; self.sql_root=Path(sql_root)
    def status(self)->bool: return self.adapter.ledger_exists()
    def bootstrap(self)->None:
        if not self.adapter.ledger_exists(): self.adapter.execute_bootstrap((self.sql_root/'migration_ledger_bootstrap.sql').read_text(encoding='utf-8'))
        if not self.adapter.verify_bootstrap(): raise MigrationBootstrapError("migration ledger bootstrap contract verification failed.")
