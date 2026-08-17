from registries.nngla.spatial_fabric.bundle17n.postgresql_contract import load_schema17n_sql,qualify_schema17n_sql
def test_postgresql_contract_is_additive_transactional_and_host_agnostic():
    assert qualify_schema17n_sql(load_schema17n_sql())==()
