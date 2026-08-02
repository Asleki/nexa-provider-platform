from pathlib import Path
from database.migration_control.service import MigrationControlService
from database.migration_control.ledger import MemoryMigrationLedger
ROOT=Path('database/migrations')
def test_status_and_verify_are_read_only():
 l=MemoryMigrationLedger(False); s=MigrationControlService(ROOT,ROOT/'migration_manifest.json',l); assert s.status().pending_migrations==4; assert s.verify().ledger_state=='NOT_BOOTSTRAPPED'; assert not l.is_bootstrapped()
