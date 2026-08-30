from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FORWARD = ROOT / "database/migrations/m006_07_11_nngla_city_parent_containment_qualification.sql"
ROLLBACK = ROOT / "database/migrations/m006_07_11_nngla_city_parent_containment_qualification_rollback.sql"
LOCKED_CITY = ROOT / "database/migrations/m006_07_11_nngla_city_spatial_foundation.sql"


def test_sequence25_adds_containment_evidence_without_replacing_city_authority_tables():
    text = FORWARD.read_text(encoding="utf-8")
    assert "CREATE TABLE geography.nngla_city_parent_containment_qualification" in text
    assert "CREATE VIEW geography.nngla_city_parent_containment_read_v1" in text
    assert "CREATE OR REPLACE VIEW geography.nngla_city_public_read_v1" in text
    assert "CREATE TABLE geography.nngla_city_geometry_record" not in text
    assert "CREATE TABLE geography.nngla_city_publication" not in text
    assert "ST_SnapToGrid" not in text
    assert "nngla_city_feature_qualification" not in text


def test_qualification_contract_persists_measurements_policy_and_exact_parent_binding():
    text = FORWARD.read_text(encoding="utf-8")
    for token in (
        "parent_region_geometry_id",
        "parent_region_geometry_sha256",
        "source_outside_parent_m2",
        "source_outside_parent_ratio",
        "normalized_outside_parent_m2",
        "normalized_outside_parent_ratio",
        "absolute_residue_max_m2",
        "ratio_residue_max",
        "qualification_basis_code",
        "qualification_policy_version",
        "realized_geometry_sha256",
    ):
        assert token in text


def test_public_view_requires_strict_covered_or_exact_matching_qualified_evidence():
    text = FORWARD.read_text(encoding="utf-8")
    assert "ST_CoveredBy(g.geometry, region_geometry.geometry)" in text
    assert "OR EXISTS" in text
    assert "q.city_geometry_id = g.city_geometry_id" in text
    assert "q.realized_geometry_sha256 = g.geometry_sha256" in text
    assert "q.parent_region_geometry_sha256 = g.parent_region_geometry_sha256" in text
    assert "q.qualification_status = 'QUALIFIED'" in text
    assert "q.normalized_outside_parent_m2 <= q.absolute_residue_max_m2" in text
    assert "q.normalized_outside_parent_ratio <= q.ratio_residue_max" in text


def test_rollback_restores_strict_view_and_drops_only_additive_objects_without_cascade():
    text = ROLLBACK.read_text(encoding="utf-8")
    lower = text.lower()
    assert lower.startswith("begin;") and lower.rstrip().endswith("commit;")
    assert " cascade" not in lower
    assert "ST_CoveredBy(g.geometry, region_geometry.geometry)" in text
    assert "DROP VIEW IF EXISTS geography.nngla_city_parent_containment_read_v1" in text
    assert "DROP TABLE IF EXISTS geography.nngla_city_parent_containment_qualification" in text
    assert "DROP TABLE IF EXISTS geography.nngla_city_geometry_record" not in text
    assert "DROP TABLE IF EXISTS geography.nngla_region_geometry_record" not in text


def test_locked_sequence24_still_contains_original_strict_contract():
    text = LOCKED_CITY.read_text(encoding="utf-8")
    assert "CREATE TABLE geography.nngla_city_geometry_record" in text
    assert "ST_CoveredBy(g.geometry, region_geometry.geometry)" in text
    assert "nngla_city_parent_containment_qualification" not in text


def test_policy_thresholds_and_status_basis_alignment_are_database_governed():
    text = FORWARD.read_text(encoding="utf-8")
    assert "CHECK (qualification_policy_version = 1)" in text
    assert "CHECK (absolute_residue_max_m2 = 0.001::double precision)" in text
    assert "CHECK (ratio_residue_max = 1e-12::double precision)" in text
    assert "qualification_status = 'QUALIFIED' AND qualification_basis_code IN" in text
    assert "qualification_status = 'REJECTED' AND qualification_basis_code IN" in text
    assert "SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE" in text
    assert "SINGLE_INTERSECTION_NUMERICAL_RESIDUE" in text
