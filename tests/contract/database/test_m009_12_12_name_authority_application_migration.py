from pathlib import Path
ROOT=Path(__file__).parents[3]
def test_application_migration_defines_receipts_change_journal_and_runtime_guards():
    sql=(ROOT/"database/migrations/m009_12_12_name_authority_application.sql").read_text()
    for token in ("name_authority_command_receipt","name_authority_change_journal","name_authority_sync_receipt","CHECK (runtime_mode IN ('production','simulation'))","change_sequence"):
        assert token in sql
def test_application_rollback_removes_only_bundle_d_tables():
    sql=(ROOT/"database/migrations/m009_12_12_name_authority_application_rollback.sql").read_text()
    assert "name_authority_record" not in sql and "canonical_name" not in sql
    assert sql.count("DROP TABLE IF EXISTS") == 3
