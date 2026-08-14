from pathlib import Path
from registries.nngla.schema15c_contract import REQUIRED_15C_TABLES,load_schema15c_sql,qualify_schema15c_sql

def test_bundle15c_schema_is_additive_complete_and_keeps_land_objects_separate():
    sql=load_schema15c_sql(); assert qualify_schema15c_sql(sql)==()
    low=sql.lower()
    assert len(REQUIRED_15C_TABLES)==6
    assert 'nngla_parcel' in low and 'nngla_title' in low and 'nngla_state_land' in low
    assert 'nngla_cadastral_geometry_assignment' in low and 'nngla_parcel_lineage' in low

def test_bundle15c_schema_does_not_redeclare_postgis_modify_migration_manifest_or_embed_consumer_real_estate_domains():
    sql=load_schema15c_sql().lower()
    assert 'create extension' not in sql
    assert 'migration_manifest' not in sql
    assert 'soko' not in sql and 'nre-' not in sql and 'listing_id' not in sql
    manifest=Path(__file__).resolve().parents[3]/'database'/'migrations'/'migration_manifest.json'
    if manifest.exists():
        assert 'nngla_cadastre_titles_state_land' not in manifest.read_text(encoding='utf-8')
