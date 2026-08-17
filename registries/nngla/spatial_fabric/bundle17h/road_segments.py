"""Bundle 17H deterministic subordinate segment candidates for locked canonical roads."""
from __future__ import annotations

from ._shared import ALIGNMENT_PATH, ROAD_SOURCE_PATH, csv_rows, stable_id
from .contracts import RoadSegmentCandidate


def derive_road_segment_candidates() -> tuple[RoadSegmentCandidate, ...]:
    source_by_candidate = {row["road_candidate_id"]: row for row in csv_rows(ROAD_SOURCE_PATH)}
    aligned = [row for row in csv_rows(ALIGNMENT_PATH) if row["object_family"] == "ROAD"]
    out: list[RoadSegmentCandidate] = []
    for row in sorted(aligned, key=lambda item: int(item["canonical_ordinal"])):
        source = source_by_candidate[row["candidate_id"]]
        segment_id = stable_id("roadseg:nngla:", row["canonical_id"], "WHOLE_ROAD_SCOPE", "1")
        out.append(RoadSegmentCandidate(
            road_segment_id=segment_id,
            road_id=row["canonical_id"],
            source_road_candidate_id=row["candidate_id"],
            segment_sequence=1,
            segment_role="PROVISIONAL_WHOLE_ROAD_ADDRESS_SCOPE",
            geometry_id=row["geometry_id"],
            start_measure_m="",
            end_measure_m="",
            geometry_status="GEOMETRY_LINKED" if row["geometry_id"] else "DEFERRED_NO_ROAD_GEOMETRY",
            addressing_scope_eligible=source["addressing_eligible"].lower() == "true",
            runtime_effect_scope="SHARED_REFERENCE",
            source_reference="P006.7.11.7.9 canonical road alignment + locked road reference candidate",
        ))
    ids = [row.road_segment_id for row in out]
    if len(out) != 350 or len(ids) != len(set(ids)):
        raise ValueError("Bundle 17H must derive exactly one non-destructive baseline segment candidate for each locked canonical road")
    return tuple(out)


def road_segment_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "road_segment_id": row.road_segment_id,
        "road_id": row.road_id,
        "source_road_candidate_id": row.source_road_candidate_id,
        "segment_sequence": str(row.segment_sequence),
        "segment_role": row.segment_role,
        "geometry_id": row.geometry_id,
        "start_measure_m": row.start_measure_m,
        "end_measure_m": row.end_measure_m,
        "geometry_status": row.geometry_status,
        "addressing_scope_eligible": str(row.addressing_scope_eligible).lower(),
        "runtime_effect_scope": row.runtime_effect_scope,
        "source_reference": row.source_reference,
    } for row in derive_road_segment_candidates())


__all__ = ["derive_road_segment_candidates", "road_segment_rows"]
