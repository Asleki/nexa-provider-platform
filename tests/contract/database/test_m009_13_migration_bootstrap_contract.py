from pathlib import Path
SQL=Path('database/migration_control/sql/migration_ledger_bootstrap.sql').read_text().lower()
def test_bootstrap_is_narrow_and_has_required_integrity():
    assert 'create schema if not exists platform' in SQL
    assert 'platform.schema_migration' in SQL
    assert 'reference.' not in SQL
    assert 'cascade' not in SQL
    for token in ('migration_id','checksum_sha256','status','sequence_number','execution_id'):
        assert token in SQL
