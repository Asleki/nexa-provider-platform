from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def test_forward_migration_contains_generation_recovery_and_read_model_objects():
    sql=(ROOT/"database/migrations/m009_12_09_name_authority_generation.sql").read_text()
    for token in ("name_generation_source_snapshot","name_generation_batch","name_generation_checkpoint","name_generation_result","name_authority_read_model","name_authority_projection_checkpoint","UNIQUE(generation_batch_id,checkpoint_sequence)","PRIMARY KEY(generation_batch_id,generation_sequence)"):
        assert token in sql
    assert "runtime_mode='simulation'" in sql

def test_rollback_drops_all_bundle_c_objects_without_touching_bundle_b():
    sql=(ROOT/"database/migrations/m009_12_09_name_authority_generation_rollback.sql").read_text()
    assert "DROP TABLE IF EXISTS reference.name_generation_batch" in sql
    assert "manual_name_candidate" not in sql and "name_authority_record" not in sql
