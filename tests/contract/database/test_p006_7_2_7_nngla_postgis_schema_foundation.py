from pathlib import Path
from registries.nngla.schema_contract import *


def test_nngla_postgis_schema_foundation_is_complete_and_not_registered_as_migration():
    sql=load_schema_sql()
    assert qualify_schema_sql(sql)==()
    assert "geometry.nngla" not in sql.lower()
    manifest=(Path(__file__).resolve().parents[3]/"database"/"migrations"/"migration_manifest.json").read_text()
    assert "nngla_spatial_foundation" not in manifest


def test_schema_keeps_source_staging_quarantine_canonical_and_geometry_separate():
    sql=load_schema_sql().lower()
    for table in REQUIRED_TABLES: assert table in sql
    assert "geometry(geometry, 4326)" in sql
    assert "unique (dataset_id, dataset_version, source_record_id, runtime_mode, effect_scope)" in sql
