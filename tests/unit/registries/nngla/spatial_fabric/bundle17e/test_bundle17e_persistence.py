import inspect

from registries.nngla.spatial_fabric.bundle17e import PostgreSQLSpatialRepository


def test_postgresql_adapter_reuses_locked_generic_tables_and_never_destructively_updates_earlier_domains():
    source = inspect.getsource(PostgreSQLSpatialRepository)
    for required in (
        "geography.nngla_spatial_feature",
        "geography.nngla_geometry_version",
        "geography.nngla_geometry_authority_record",
        "geography.nngla_canonical_crosswalk",
        "geography.nngla_execution_receipt",
        "geography.nngla_execution_item",
    ):
        assert required in source
    lowered = source.lower()
    assert "update geography.nngla_place_reference" not in lowered
    assert "update geography.nngla_road" not in lowered
    assert "update geography.nngla_administrative_area" not in lowered
    assert "delete from geography." not in lowered


def test_postgis_point_write_uses_governed_4326_point_without_modifying_subject_identity():
    source = inspect.getsource(PostgreSQLSpatialRepository.persist_point)
    assert "ST_SetSRID(ST_MakePoint" in source
    assert "NG-CRS-EPSG4326" in source
    assert "SPATIAL_REFERENCE_POINT" in source
