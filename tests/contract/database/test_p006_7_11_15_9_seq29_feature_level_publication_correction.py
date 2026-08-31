from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIG = ROOT / "database/migrations/m006_07_11_nngla_feature_level_spatial_publication_correction.sql"

LOCKED = {
    "m006_07_11_nngla_municipality_spatial_publication.sql": "e4718bbd566c42fb83bbb8a356982844e82658a48503881b703d787b9aadc809",
    "m006_07_11_nngla_municipality_spatial_publication_rollback.sql": "1e3401b998affe8a38280dbcf0b2e6f7eec42193524cc41203387d849c8711ae",
    "m006_07_11_nngla_city_district_spatial_publication.sql": "75b700c3923e27d67ecb6c44587643c895f5f3664b2d1da501804e27cb37aaaf",
    "m006_07_11_nngla_city_district_spatial_publication_rollback.sql": "384060d3b05510a723b6c63aa5b7d0867738354286c14e40efd4a647f936222f",
    "m006_07_11_nngla_town_settlement_footprint_publication.sql": "58574b71c38c36d27d4005bbb94055cfd1253fa6db9f8c11f85fda42912679c6",
    "m006_07_11_nngla_town_settlement_footprint_publication_rollback.sql": "01f951e394e633e81e01734ab027101ee92189d49eb22b0ac7f74524d6bbdf3f",
}


def test_applied_26_28_bytes_remain_immutable():
    for name, expected in LOCKED.items():
        assert sha256((ROOT / "database/migrations" / name).read_bytes()).hexdigest() == expected


def test_seq29_separates_feature_publication_from_fabric_completeness():
    s = MIG.read_text()
    for token in (
        "nngla_municipality_feature_qualification",
        "nngla_municipality_feature_publication",
        "nngla_city_district_feature_qualification",
        "nngla_city_district_feature_publication",
        "nngla_municipality_fabric_status_read_v2",
        "nngla_city_district_fabric_status_read_v2",
        "nngla_municipality_public_read_v2",
        "nngla_city_district_public_read_v2",
        "nngla_town_public_read_v2",
    ):
        assert token in s
    assert "ST_Equals" in s
    assert "sibling_positive_overlap_m2=0" in s
    assert "municipality_sibling_positive_overlap_m2=0" in s


def test_seq29_public_v2_views_do_not_require_complete_fabric():
    s = MIG.read_text()
    district = s.split("CREATE VIEW geography.nngla_city_district_public_read_v2 AS", 1)[1].split(
        "CREATE VIEW geography.nngla_municipality_public_read_v2 AS", 1
    )[0]
    municipality = s.split("CREATE VIEW geography.nngla_municipality_public_read_v2 AS", 1)[1].split(
        "CREATE VIEW geography.nngla_town_public_read_v2 AS", 1
    )[0]
    assert "partition_status='COMPLETE'" not in district
    assert "fabric_status='COMPLETE'" not in district
    assert "partition_status='COMPLETE'" not in municipality
    assert "fabric_status='COMPLETE'" not in municipality
    assert "LEFT JOIN geography.nngla_city_district_fabric_status_read_v2" in district
    assert "LEFT JOIN geography.nngla_municipality_fabric_status_read_v2" in municipality


def test_town_v2_requires_current_published_municipality_only():
    s = MIG.read_text()
    town = s.split("CREATE VIEW geography.nngla_town_public_read_v2 AS", 1)[1]
    assert "nngla_municipality_public_read_v2" in town
    assert "nngla_city_district" not in town
    assert "ST_CoveredBy(f.geometry,parent_municipality.geometry)" in town



def test_publication_eligible_views_require_governed_production_execution_receipts():
    s = MIG.read_text()
    district = s.split("CREATE VIEW geography.nngla_city_district_public_read_v2 AS", 1)[1].split(
        "CREATE VIEW geography.nngla_municipality_public_read_v2 AS", 1
    )[0]
    municipality = s.split("CREATE VIEW geography.nngla_municipality_public_read_v2 AS", 1)[1].split(
        "CREATE VIEW geography.nngla_town_public_read_v2 AS", 1
    )[0]
    town = s.split("CREATE VIEW geography.nngla_town_public_read_v2 AS", 1)[1]

    expected = (
        (district, "p006.7.11.15.9-seq29-city-district-feature-publication"),
        (municipality, "p006.7.11.15.9-seq29-municipality-feature-publication"),
        (town, "p006.7.11.15.9-seq29-town-feature-publication"),
    )
    for view_sql, plan_id in expected:
        assert "geography.nngla_execution_receipt" in view_sql
        assert "geography.nngla_execution_item" in view_sql
        assert f"er.plan_id='{plan_id}'" in view_sql
        assert "er.plan_version=1" in view_sql
        assert "er.runtime_mode='production'" in view_sql
        assert "er.status IN ('APPLIED','REUSED')" in view_sql
        assert "ei.publication_ready" in view_sql
        assert "ei.detail->>'publication_id'" in view_sql
        assert "ei.detail->>'geometry_sha256'" in view_sql

def test_seq29_manifest_is_exact_append_only_tail():
    manifest = json.loads((ROOT / "database/migrations/migration_manifest.json").read_text())
    assert int(manifest["catalogue_version"]) == 13
    rows = manifest["migrations"]
    assert [int(row["sequence_number"]) for row in rows[-4:]] == [26, 27, 28, 29]
    row = rows[-1]
    assert row["migration_id"] == "m006_07_11_nngla_feature_level_spatial_publication_correction"
    assert row["depends_on"] == ["m006_07_11_nngla_town_settlement_footprint_publication"]
    forward = ROOT / "database/migrations" / row["forward_file"]
    rollback = ROOT / "database/migrations" / row["rollback_file"]
    assert row["forward_sha256"] == sha256(forward.read_bytes()).hexdigest()
    assert row["rollback_sha256"] == sha256(rollback.read_bytes()).hexdigest()
    assert int(row["forward_byte_size"]) == forward.stat().st_size
    assert int(row["rollback_byte_size"]) == rollback.stat().st_size
