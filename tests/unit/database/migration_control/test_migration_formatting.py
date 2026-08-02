from database.migration_control.service import MigrationStatus
from database.migration_control.formatting import format_status,format_json
def test_formats_are_stable_and_machine_readable():
 s=MigrationStatus('NOT_BOOTSTRAPPED',4,0,4,0,0,0,0,'a'*64); assert 'Pending migrations: 4' in format_status(s); assert 'ledger_state' in format_json(s)
