from registries.nngla.spatial_fabric.bundle19a.postgresql_contract import bundle19a_requires_schema_migration, existing_schema_findings


def test_existing_locked_postgresql_contract_has_all_required_capabilities():
    assert existing_schema_findings() == ()


def test_bundle19a_requires_no_schema_migration():
    assert bundle19a_requires_schema_migration() is False
