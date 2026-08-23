from pathlib import Path
from database.migration_control.service import MigrationControlService
from database.migration_control.ledger import MemoryMigrationLedger
ROOT=Path('database/migrations')
def test_fresh_database_status_is_read_only():
    ledger=MemoryMigrationLedger(bootstrapped=False)
    s=MigrationControlService(ROOT,ROOT/'migration_manifest.json',ledger)
    result=s.status()
    assert result.ledger_state=='NOT_BOOTSTRAPPED'
    assert result.repository_migrations==20
    assert result.applied_migrations==0
    assert result.pending_migrations==20
    assert ledger.is_bootstrapped() is False

def test_plan_is_deterministic():
    s=MigrationControlService(ROOT,ROOT/'migration_manifest.json',MemoryMigrationLedger(False))
    a=s.plan(); b=s.plan()
    assert a.plan_checksum==b.plan_checksum
    assert [d.identity.sequence_number for d in a.forward_order]==list(range(1,21))
