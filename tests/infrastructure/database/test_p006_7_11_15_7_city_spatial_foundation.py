from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "database/migrations/m006_07_11_nngla_city_spatial_foundation.sql"


def source() -> str:
    return MIGRATION.read_text()


def test_city_foundation_is_new_additive_authority_and_explicitly_independent_from_delivery_1_3():
    text = source()
    assert "CREATE TABLE geography.nngla_city_geometry_record" in text
    assert "CREATE TABLE geography.nngla_city_publication" in text
    assert "CREATE VIEW geography.nngla_city_public_read_v1" in text
    for historical in (
        "nngla_city_feature_qualification",
        "nngla_administrative_geometry_adoption_decision",
        "nngla_administrative_geometry_assignment",
        "nngla_city_authority_receipt",
    ):
        assert historical in text
    assert "DROP TABLE" not in text.upper()
    assert "ALTER TABLE geography.nngla_region_geometry_record" not in text


def test_city_geometry_contract_binds_final_geometry_to_exact_parent_region_and_provenance():
    text = source()
    for token in (
        "parent_region_id",
        "parent_region_geometry_id",
        "parent_region_geometry_sha256",
        "source_dataset_sha256",
        "source_geometry_sha256",
        "realization_method",
        "realization_version",
        "geometry_sha256",
        "area_m2",
        "perimeter_m",
        "label_point",
    ):
        assert token in text
    assert "'SOURCE_REUSE'" in text
    assert "'PARENT_CONTAINED_NORMALIZATION'" in text
    assert "ST_CoveredBy(label_point, geometry)" in text


def test_public_city_view_is_fail_closed_on_current_qualified_parent_and_publication():
    text = source()
    assert "region_geometry.geometry_sha256 = g.parent_region_geometry_sha256" in text
    assert "region_geometry.effective_to IS NULL" in text
    assert "region_geometry.qualification_status = 'QUALIFIED'" in text
    assert "p.publication_status = 'PUBLISHED'" in text
    assert "city_admin.administrative_type_code = 'CITY'" in text
    assert "ST_CoveredBy(g.geometry, region_geometry.geometry)" in text
    assert "g.canonical_name = city_admin.canonical_name" in text
    assert "city_admin.region_code = region_admin.region_code" in text
    assert "FOREIGN KEY (city_geometry_id, administrative_area_id)" in text
