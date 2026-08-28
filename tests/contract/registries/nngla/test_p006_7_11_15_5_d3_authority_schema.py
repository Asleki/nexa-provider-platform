from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[4]
SQL = ROOT / "database/migrations/m006_07_11_nngla_administrative_authority_adoption.sql"
ROLLBACK = ROOT / "database/migrations/m006_07_11_nngla_administrative_authority_adoption_rollback.sql"
MANIFEST = ROOT / "database/migrations/migration_manifest.json"


def test_d3_r1_schema_is_feature_level_not_region_foundation():
    text = SQL.read_text().lower()
    assert "nngla_city_feature_qualification" in text
    assert "nngla_administrative_geometry_assignment" in text
    assert "nngla_unresolved_territorial_residual" in text
    assert "nngla_administrative_fabric_completeness" in text
    assert "nngla_region_foundation" not in text
    assert "national_regions" not in text


def test_d3_r1_schema_keeps_feature_and_fabric_status_distinct():
    text = SQL.read_text()
    assert "feature_qualification_status" in text
    assert "completeness_status" in text
    assert "FEATURE_QUALIFIED" in text and "PARTIAL" in text and "COMPLETE" in text


def test_d3_r1_runtime_is_production_coherent():
    text = SQL.read_text()
    assert "runtime_mode text NOT NULL CHECK (runtime_mode='production')" in text
    assert "runtime_mode IN ('simulation','production')" in text  # fabric metadata may describe both runtimes


def test_d3_r1_rollback_drops_only_d3_objects():
    text = ROLLBACK.read_text().lower()
    assert "nngla_shared_face" not in text
    assert "nngla_geometry_version" not in text
    assert "nngla_city_feature_qualification" in text
