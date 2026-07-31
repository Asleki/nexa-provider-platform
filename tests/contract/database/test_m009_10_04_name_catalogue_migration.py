from pathlib import Path
SQL=Path("database/migrations/m009_10_04_name_catalogue.sql").read_text()
def test_migration_matches_locked_identity_contract():
    assert "name_id TEXT PRIMARY KEY" in SQL
    assert "UNIQUE(runtime_mode,name_kind,search_value)" in SQL.replace(" ","")
def test_runtime_is_extensible_and_metadata_is_jsonb():
    assert "runtime_mode ~" in SQL and "IN ('simulation','production')" not in SQL
    assert "attributes JSONB" in SQL
