from datetime import datetime,timezone
import pytest
from database.migration_control.ledger import MigrationLedgerRecord,MemoryMigrationLedger
from database.migration_control.errors import MigrationLedgerError

def rec(summary=None): return MigrationLedgerRecord('m','M','m.sql',1,'a'*64,'STARTED','e',datetime.now(timezone.utc),error_summary=summary)
def test_ledger_transitions_and_uniqueness():
 l=MemoryMigrationLedger(); l.insert_started(rec()); l.mark_applied('m',completed_at=datetime.now(timezone.utc),duration_ms=1); assert l.get('m').status=='APPLIED'
 with pytest.raises(MigrationLedgerError): l.insert_started(rec())
def test_ledger_blocks_secret_material():
 with pytest.raises(MigrationLedgerError): rec('postgresql://u:p@h/d')
