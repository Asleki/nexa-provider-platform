from registries.nngla.schema15b_contract import load_schema15b_sql,qualify_schema15b_sql,REQUIRED_15B_TABLES

def test_bundle15b_schema_is_additive_and_complete():
    sql=load_schema15b_sql(); assert qualify_schema15b_sql(sql)==()
    for table in REQUIRED_15B_TABLES: assert f'CREATE TABLE {table}' in sql

def test_bundle15b_schema_does_not_redeclare_postgis_or_locked_migration_manifest():
    sql=load_schema15b_sql().lower()
    assert 'create extension' not in sql
    assert 'migration_manifest' not in sql
    assert 'site_id text primary key' in sql
    assert 'parcel_id text' in sql
