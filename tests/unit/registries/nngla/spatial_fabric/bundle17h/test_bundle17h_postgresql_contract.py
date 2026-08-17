from registries.nngla.spatial_fabric.bundle17h import load_schema17h_sql, qualify_schema17h_sql


def test_bundle17h_postgresql_contract_has_scoped_unique_number_and_row_locked_allocator():
    sql = load_schema17h_sql()
    assert qualify_schema17h_sql(sql) == ()
    n = sql.lower()
    assert "unique (series_id, normalized_number_key)" in n
    assert "for update" in n
    assert "create or replace function geography.nngla_reserve_address_number" in n
    assert "nngla_address_id_sequence" in n and "nextval" in n
    assert "ng-adr-" in n


def test_bundle17h_backend_contract_is_host_and_domain_agnostic_for_later_dns_pwa_deployment():
    sql = load_schema17h_sql().lower()
    assert "nexaecosystem.com" not in sql
    assert "localhost" not in sql
    assert "namecheap" not in sql
