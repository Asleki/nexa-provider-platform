from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FORWARD = ROOT / (
    "database/migrations/"
    "m006_07_11_nngla_municipality_public_read_"
    "qualification_admission_correction.sql"
)

ROLLBACK = ROOT / (
    "database/migrations/"
    "m006_07_11_nngla_municipality_public_read_"
    "qualification_admission_correction_rollback.sql"
)


def test_seq30_scope_is_municipality_only():
    sql = FORWARD.read_text()

    assert (
        "CREATE OR REPLACE VIEW "
        "geography.nngla_municipality_public_read_v2"
    ) in sql

    assert "nngla_city_district_public_read_v2" not in sql
    assert "nngla_town_public_read_v2" not in sql


def test_seq30_removes_only_duplicate_municipality_spatial_admission():
    sql = FORWARD.read_text()

    assert "ST_CoveredBy(g.geometry,r.geometry)" not in sql
    assert "ST_Intersection(g.geometry,c.geometry)" not in sql

    # Independent read-time label safety remains.
    assert "ST_CoveredBy(g.label_point,g.geometry)" in sql

    # Governed feature qualification remains authoritative.
    assert "fq.qualification_status='QUALIFIED'" in sql
    assert "fq.covered_by_parent_region" in sql
    assert "fq.city_positive_overlap_m2=0" in sql
    assert "fq.municipality_sibling_positive_overlap_m2=0" in sql

    # Governed publication + production receipt remain mandatory.
    assert "publication_status='PUBLISHED'" in sql
    assert "geography.nngla_execution_receipt" in sql
    assert "geography.nngla_execution_item" in sql
    assert "ei.publication_ready" in sql


def test_seq30_rollback_restores_sequence29_predicates():
    sql = ROLLBACK.read_text()

    assert "ST_CoveredBy(g.geometry,r.geometry)" in sql
    assert "ST_Intersection(g.geometry,c.geometry)" in sql


def test_seq30_manifest_entry_matches_files():
    manifest = json.loads(
        (ROOT / "database/migrations/migration_manifest.json").read_text()
    )

    rows = [
        row for row in manifest["migrations"]
        if int(row["sequence_number"]) == 30
    ]

    assert len(rows) == 1
    row = rows[0]

    assert row["migration_id"] == (
        "m006_07_11_nngla_municipality_public_read_"
        "qualification_admission_correction"
    )

    assert row["expected_objects"]["views"] == [
        "geography.nngla_municipality_public_read_v2"
    ]

    assert row["forward_sha256"] == sha256(FORWARD.read_bytes()).hexdigest()
    assert row["rollback_sha256"] == sha256(ROLLBACK.read_bytes()).hexdigest()
