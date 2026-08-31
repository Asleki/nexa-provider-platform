from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
SQL = (ROOT / "database/migrations/m006_07_11_nngla_municipality_spatial_publication.sql").read_text(encoding="utf-8")

def test_migration_creates_required_municipality_contracts():
    for token in (
        "geography.nngla_municipality_geometry_record",
        "geography.nngla_municipality_partition_qualification",
        "geography.nngla_municipality_publication",
        "geography.nngla_municipality_public_read_v1",
    ):
        assert token in SQL

def test_complete_gate_is_exact_and_member_bound():
    assert "municipality_sibling_positive_overlap_m2=0" in SQL
    assert "city_municipality_positive_overlap_m2=0" in SQL
    assert "union_equals_region" in SQL
    assert "jsonb_array_elements(q.municipality_member_set)" in SQL
    assert "absolute_residue_max" not in SQL
