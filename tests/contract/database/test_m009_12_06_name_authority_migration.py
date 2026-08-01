from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def test_migration_creates_only_new_authority_objects_with_runtime_and_identity_safety():
 sql=(ROOT/"database/migrations/m009_12_06_name_authority.sql").read_text()
 for token in ("manual_name_candidate","name_authority_record","name_authority_component","UNIQUE(runtime_mode,composition_key)","REFERENCES reference.canonical_name(name_id)"): assert token in sql
 assert "ALTER TABLE reference.canonical_name" not in sql
def test_rollback_drops_children_before_parents():
 sql=(ROOT/"database/migrations/m009_12_06_name_authority_rollback.sql").read_text(); assert sql.index("name_authority_component")<sql.index("name_authority_record")<sql.index("manual_name_candidate")
