"""Execution of one trusted migration artifact."""
from __future__ import annotations
from datetime import datetime,timezone
from time import monotonic
from uuid import uuid4
from pathlib import Path
from .constants import RUNNER_VERSION
from .errors import MigrationExecutionError
from .ledger import MigrationLedgerRecord
from .sanitization import sanitize_text
class MigrationExecutor:
    def __init__(self,adapter,migration_root:Path): self.adapter=adapter; self.migration_root=Path(migration_root)
    def execute(self,definition,ledger,*,applied_by,database_name,environment_name,repository_revision='unknown'):
        existing=ledger.get(definition.identity.migration_id)
        if existing is not None: raise MigrationExecutionError("migration already has a ledger record.")
        started=datetime.now(timezone.utc); t=monotonic()
        record=MigrationLedgerRecord(migration_id=definition.identity.migration_id,milestone_id=definition.identity.milestone_id,filename=definition.forward.relative_path,sequence_number=definition.identity.sequence_number,checksum_sha256=definition.forward.sha256,status='STARTED',execution_id=str(uuid4()),started_at=started,applied_by=applied_by,database_name=database_name,environment_name=environment_name,runner_version=RUNNER_VERSION,repository_revision=repository_revision)
        ledger.insert_started(record)
        try:
            sql=(self.migration_root/definition.forward.relative_path).read_text(encoding='utf-8')
            self.adapter.execute_migration(sql,definition.forward.transaction_policy)
        except Exception as exc:
            duration=max(0,int((monotonic()-t)*1000)); message=sanitize_text(exc)
            ledger.mark_failed(record.migration_id,completed_at=datetime.now(timezone.utc),duration_ms=duration,error_code='MIGRATION_EXECUTION_FAILED',error_summary=message)
            raise MigrationExecutionError(f"Migration {record.migration_id} failed.") from exc
        duration=max(0,int((monotonic()-t)*1000)); ledger.mark_applied(record.migration_id,completed_at=datetime.now(timezone.utc),duration_ms=duration)
        return ledger.get(record.migration_id)
