"""Live verification of the immutable pre-17E NNGLA canonical baseline."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .candidate_state import ALIGNMENT_PATH
from .contracts import BaselineVerificationReport

BOUNDARY_SOURCE_PACKAGE = Path(
    "data/novegeo/geography/world-boundary/provenance/novegeo_world_boundary_v002_source-package.json"
)


def _alignment_rows(root: Path) -> tuple[dict[str, str], ...]:
    with (root / ALIGNMENT_PATH).open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def _query_pairs(connection, sql: str) -> dict[str, str]:
    with connection.cursor() as cur:
        cur.execute(sql)
        return {str(a): str(b) for a, b in cur.fetchall()}


def verify_immutable_baseline(root: Path, connection) -> BaselineVerificationReport:
    """Verify expected identities without rejecting legitimate future additions."""
    rows = _alignment_rows(root)
    findings: list[str] = []
    missing: list[str] = []
    conflicts: list[str] = []
    matched = 0

    actual_by_family = {
        "PLACE": _query_pairs(
            connection,
            "SELECT source_place_code, place_id FROM geography.nngla_place_reference",
        ),
        "ADMINISTRATIVE_AREA": _query_pairs(
            connection,
            "SELECT administrative_candidate_id, administrative_area_id FROM geography.nngla_administrative_area",
        ),
        "ROAD": _query_pairs(
            connection,
            "SELECT source_candidate_id, road_id FROM geography.nngla_road",
        ),
        "GEOGRAPHIC_FEATURE": _query_pairs(
            connection,
            "SELECT feature_id, feature_id FROM geography.nngla_spatial_feature "
            "WHERE feature_id ~ '^NG-FEAT-[0-9]{6}$'",
        ),
        "EXISTING_GEOMETRY": _query_pairs(
            connection,
            "SELECT geometry_id, geometry_id FROM geography.nngla_geometry_authority_record",
        ),
    }

    source_key_field = {
        "PLACE": "source_record_id",
        "ADMINISTRATIVE_AREA": "candidate_id",
        "ROAD": "candidate_id",
        "GEOGRAPHIC_FEATURE": "candidate_id",
        "EXISTING_GEOMETRY": "candidate_id",
    }

    for row in rows:
        family = row["object_family"]
        if family not in actual_by_family:
            findings.append(f"UNSUPPORTED_ALIGNMENT_FAMILY:{family}")
            continue
        source_key = row[source_key_field[family]]
        expected = row["canonical_id"]
        actual = actual_by_family[family].get(source_key)
        marker = f"{family}:{source_key}->{expected}"
        if actual is None:
            missing.append(marker)
        elif actual != expected:
            conflicts.append(f"{marker}:ACTUAL={actual}")
        else:
            matched += 1

    source = json.loads((root / BOUNDARY_SOURCE_PACKAGE).read_text(encoding="utf-8"))
    boundary_id = str(source["boundaryId"])
    with connection.cursor() as cur:
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM geography.world_boundary WHERE boundary_id=%s)",
            (boundary_id,),
        )
        sovereign_ok = bool(cur.fetchone()[0])
    if not sovereign_ok:
        findings.append(f"SOVEREIGN_BOUNDARY_MISSING:{boundary_id}")

    return BaselineVerificationReport(
        expected_count=len(rows),
        matched_count=matched,
        missing=tuple(missing),
        conflicts=tuple(conflicts),
        sovereign_boundary_ok=sovereign_ok,
        findings=tuple(findings),
    )


__all__ = ["BOUNDARY_SOURCE_PACKAGE", "verify_immutable_baseline"]
