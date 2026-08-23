"""Load locked Bundle 20A predecessors without inventing canonical road identities."""
from __future__ import annotations
from collections import Counter
from ._shared import *


def canonical_road_rows() -> tuple[dict[str, str], ...]:
    aligned = [r for r in csv_rows(CANONICAL_ALIGNMENT) if r["object_family"] == "ROAD"]
    aligned.sort(key=lambda r: int(r["canonical_ordinal"]))
    if len(aligned) != EXPECTED_ROAD_COUNT:
        raise ValueError(f"expected {EXPECTED_ROAD_COUNT} locked canonical road alignments")
    source = {r["road_candidate_id"]: r for r in csv_rows(ROAD_SOURCE)}
    result = []
    for a in aligned:
        row = dict(source[a["candidate_id"]])
        row["road_id"] = a["canonical_id"]
        result.append(row)
    counts = Counter(r["road_class_code"] for r in result)
    if dict(counts) != EXPECTED_CLASS_COUNTS:
        raise ValueError(f"canonical road class counts changed: {dict(counts)}")
    return tuple(result)


def place_rows() -> tuple[dict[str, str], ...]:
    rows = csv_rows(PLACE_POINTS)
    if len(rows) != 700:
        raise ValueError("Bundle 19A place reference-point baseline must contain 700 rows")
    return rows


def region_features() -> tuple[dict, ...]:
    payload = json_payload(ADMIN_BOUNDARIES)
    rows = tuple(f for f in payload["features"] if f["properties"]["administrative_type_code"] == "REGION")
    if len(rows) != 8:
        raise ValueError("Bundle 19B must provide eight region boundaries")
    return rows


def source_hashes() -> tuple[tuple[str, str], ...]:
    return tuple((str(p.relative_to(ROOT)), sha256_path(p)) for p in INPUT_PATHS if p.exists())
