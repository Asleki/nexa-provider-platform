from pathlib import Path
def test_rollback_is_explicit(): assert "DROP TABLE IF EXISTS reference.canonical_name" in Path("database/migrations/m009_10_04_name_catalogue_rollback.sql").read_text()
