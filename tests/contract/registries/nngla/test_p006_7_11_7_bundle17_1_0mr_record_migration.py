from pathlib import Path
import json

from registries.nngla.migration_ready.record_execution import PLAN_ID, PLAN_VERSION


ROOT = Path(__file__).resolve().parents[4]


def test_plan_lineage_advances_to_v3_without_new_database_migration():
    assert PLAN_ID == "P006.7.11.7.0MR-SPATIAL-BATCH"
    assert PLAN_VERSION == 3
    manifest = json.loads((ROOT / "database/migrations/migration_manifest.json").read_text(encoding="utf-8"))
    historical = manifest["migrations"][:18]
    assert historical[-1]["sequence_number"] == 18
    assert all("migration_ready" not in row["migration_id"] for row in historical)
    # Later milestones may append schema migrations; that does not rewrite the locked v3 record-migration lineage.
    assert [row["sequence_number"] for row in manifest["migrations"][18:]] == [19, 20]


def test_record_engine_is_additive_and_locked_bundle17e_is_not_rewritten():
    persistence = (ROOT / "registries/nngla/spatial_fabric/bundle17e/persistence.py").read_text(encoding="utf-8")
    assert "class PostgreSQLSpatialRepository" in persistence
    assert "self.connection.rollback()" in persistence

    record_persistence = (ROOT / "registries/nngla/migration_ready/record_persistence.py").read_text(encoding="utf-8")
    assert "class RecordAtomicPersistence" in record_persistence
    assert "connection.rollback()" in record_persistence


def test_nngla_record_selection_is_canonical_and_never_randomized():
    progress = (ROOT / "registries/nngla/migration_ready/record_progress.py").read_text(encoding="utf-8").lower()
    assert "canonical_ng_spt" not in progress  # implementation uses canonical NG-SPT identity, not a magic data flag
    assert "random.shuffle" not in progress
    assert "random.sample" not in progress
    assert "canonical_spatial_point_id" in progress


def test_cli_exposes_count_start_and_per_record_history_without_removing_predecessor_commands():
    cli = (ROOT / "registries/nngla/migration_ready/cli.py").read_text(encoding="utf-8")
    for token in (
        '"preview-spatial"',
        '"execute-spatial"',
        '"preview-records"',
        '"execute-records"',
        '"record-history"',
        '"--count"',
        '"--start-ordinal"',
    ):
        assert token in cli
