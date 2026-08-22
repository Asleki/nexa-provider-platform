from csv import DictReader
from hashlib import sha256
import json

from registries.nngla.spatial_fabric.bundle19a._shared import (
    ASSIGNMENTS_PATH, FOOTPRINTS_PATH, QUALIFICATION_RESULTS_PATH, REFERENCE_POINTS_PATH, RELATIONSHIPS_PATH, SUMMARY_PATH,
)
from registries.nngla.spatial_fabric.bundle19a.artifacts import artifact_findings
from registries.nngla.spatial_fabric.bundle19a.materialize import materialize_bundle19a_artifacts


def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(DictReader(h))


def hashes(paths):
    return {str(p): sha256(p.read_bytes()).hexdigest() for p in paths}


def test_materialized_artifacts_have_exact_governed_counts_and_are_reproducible():
    assert artifact_findings() == ()
    paths = materialize_bundle19a_artifacts()
    first = hashes(paths)
    assert len(rows(REFERENCE_POINTS_PATH)) == 700
    assert len(rows(RELATIONSHIPS_PATH)) == 668
    assert len(rows(ASSIGNMENTS_PATH)) == 1119
    assert len(rows(QUALIFICATION_RESULTS_PATH)) == 700
    geo = json.loads(FOOTPRINTS_PATH.read_text(encoding="utf-8"))
    assert geo["type"] == "FeatureCollection" and len(geo["features"]) == 419
    assert all(f["properties"]["legal_boundary_status"] == "NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY" for f in geo["features"])
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["counts"] == {
        "canonical_places": 700,
        "parent_spatial_evidence": 668,
        "place_reference_points": 700,
        "point_only_explicit_outcomes": 281,
        "qualified_geometry_assignment_candidates": 1119,
        "settlement_footprints": 419,
    }
    assert summary["database_contract"]["new_schema_migration_required"] is False
    assert hashes(materialize_bundle19a_artifacts()) == first
