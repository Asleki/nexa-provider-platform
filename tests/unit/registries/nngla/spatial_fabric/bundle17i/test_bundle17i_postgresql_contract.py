from registries.nngla.spatial_fabric.bundle17i import load_schema17i_sql, qualify_schema17i_sql


def test_bundle17i_postgresql_contract_allows_null_parcel_holder_at_reservation_and_locks_series():
    sql = load_schema17i_sql()
    assert qualify_schema17i_sql(sql) == ()
    n = sql.lower()
    reservation = n.split("create table geography.nngla_title_reference_reservation",1)[1].split(");",1)[0]
    assert "parcel_id text," in reservation
    assert "holder_reference text," in reservation
    assert "for update" in n
    assert "unique (reserved_title_id)" in n
    assert "v_reserved_title_id" in n and "next_sequence" in n


def test_bundle17i_backend_contract_has_no_deployment_host_or_domain_coupling():
    n = load_schema17i_sql().lower()
    assert "nexaecosystem.com" not in n
    assert "localhost" not in n
    assert "namecheap" not in n
