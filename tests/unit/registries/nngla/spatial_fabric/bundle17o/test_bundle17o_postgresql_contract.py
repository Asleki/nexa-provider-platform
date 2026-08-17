from registries.nngla.spatial_fabric.bundle17o.postgresql_contract import load_schema17o_sql,qualify_schema17o_sql
def test_postgis_query_contract_is_read_oriented_additive_and_host_agnostic():
    assert qualify_schema17o_sql(load_schema17o_sql())==()
