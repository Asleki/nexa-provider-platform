from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _text(path):
    return (ROOT / path).read_text()


def test_city_district_writer_is_incremental_and_fabric_is_separate():
    s = _text("registries/nngla/city_district_realization/incremental.py")
    assert "require_complete_partition" not in s
    assert "SIBLING_POSITIVE_AREA_CONFLICT" in s
    assert "with self.connection.transaction()" in s
    assert "_persist_fabric" in s
    assert 'partition_status = "COMPLETE" if fabric["fabric_status"] == "COMPLETE" else "INCOMPLETE"' in s
    assert '"PARTIAL" if failed and (inserted or reused)' in s
    assert "publication_ready=False" in s


def test_municipality_writer_is_incremental_region_minus_city():
    s = _text("registries/nngla/municipality_realization/incremental.py")
    assert "ST_Difference(inside_region,city_geometry)" in s
    assert "PARENT_REGION_CONTAINMENT_FAILED" in s
    assert "MUNICIPALITY_SIBLING_POSITIVE_AREA_CONFLICT" in s
    assert "with self.connection.transaction()" in s
    assert "partition is not COMPLETE" not in s
    assert 'partition_status = "COMPLETE" if fabric["fabric_status"] == "COMPLETE" else "INCOMPLETE"' in s
    assert "publication_ready=False" in s


def test_town_writer_is_primary_per_municipality_and_national_write_is_disabled():
    s = _text("registries/nngla/town_footprint_realization/incremental.py")
    assert "def preview_municipality" in s
    assert "def execute_municipality" in s
    assert "NATIONAL_TOWN_ATOMIC_EXECUTION_DISABLED_BY_SEQUENCE_29" in s
    assert "nngla_municipality_public_read_v2" in s
    assert "nngla_city_district" not in s
    assert "len(items) != 120" not in s
    assert "TOWN national realization is not publication-ready" not in s
    assert "publication_ready=False" in s


def test_historical_operational_lock_has_exact_seq29_successor_authority():
    s = _text("tests/registries/nngla/test_p006_7_11_7_20_operational_backend_lock.py")
    assert "P006_7_11_15_9_SEQ29_PRODUCTION_SUCCESSOR_SHA256" in s
    assert "_authorized_p006_7_11_15_9_seq29_production_successor" in s
    for path in (
        "infrastructure/database/read/nngla_municipality_public_map.py",
        "infrastructure/database/read/nngla_city_district_public_map.py",
        "infrastructure/database/read/nngla_town_public_map.py",
        "infrastructure/api/services/nngla_city_district_map_read_service.py",
        "infrastructure/api/services/nngla_town_map_read_service.py",
        "infrastructure/api/app/nngla_map_extensions/layers/city_district_spatial_publication.py",
        "infrastructure/api/app/nngla_map_extensions/layers/town_settlement_footprint_publication.py",
    ):
        assert path in s


def test_seq29_fabric_sql_uses_qualified_geometry_aliases():
    district = _text(
        "registries/nngla/city_district_realization/incremental.py"
    )
    municipality = _text(
        "registries/nngla/municipality_realization/incremental.py"
    )

    assert "bool_and(ST_IsValid(src.geometry))" in district
    assert "bool_and(NOT ST_IsEmpty(src.geometry))" in district
    assert "ST_GeometryType(src.geometry)" in district
    assert "ST_CoveredBy(src.geometry,city.geometry)" in district
    assert "ST_Collect(src.geometry)) AS district_union" in district

    assert "bool_and(ST_IsValid(src.geometry))" in municipality
    assert "bool_and(NOT ST_IsEmpty(src.geometry))" in municipality
    assert "ST_GeometryType(src.geometry)" in municipality
    assert "ST_CoveredBy(src.geometry,region.geometry)" in municipality
    assert "ST_Collect(src.geometry)) AS municipality_union" in municipality
