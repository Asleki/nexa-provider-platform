from registries.nngla.schema15a_contract import load_schema15a_sql, qualify_schema15a_sql, REQUIRED_15A_TABLES

def test_bundle15a_schema_extension_is_complete_and_additive():
    sql=load_schema15a_sql()
    assert qualify_schema15a_sql(sql)==()
    assert len(REQUIRED_15A_TABLES)==4

def test_bundle15a_schema_does_not_modify_locked_migration_manifest():
    sql=load_schema15a_sql().lower()
    assert 'migration_manifest' not in sql
    assert 'drop table' not in sql
