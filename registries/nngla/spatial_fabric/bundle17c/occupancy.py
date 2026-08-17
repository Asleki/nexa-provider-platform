"""Derive reusable occupancy relations from qualified Bundle 17C source candidates."""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from registries.nngla.spatial_fabric.coordinate_occurrences import candidate_identity
from registries.nngla.spatial_fabric.bundle17b import derive_containment_qualifications

from ._shared import ROOT, SOURCE_ROOT, csv_rows, stable_id
from .contracts import RelationshipType, SpatialOccupancyRelationship

_CANDIDATE_ROOT = SOURCE_ROOT / "03_qualified_feature_candidates"
_CANDIDATE_FILES = (
    "novegeo_hill_candidates_v001.csv",
    "novegeo_mountain_candidates_v001.csv",
    "novegeo_valley_candidates_v001.csv",
    "novegeo_plateau_candidates_v001.csv",
    "novegeo_plain_candidates_v001.csv",
    "novegeo_forest_candidates_v001.csv",
    "novegeo_wetland_candidates_v001.csv",
    "novegeo_bay_candidates_v001.csv",
    "novegeo_cape_candidates_v001.csv",
    "novegeo_estuary_candidates_v001.csv",
    "novegeo_natural_harbour_candidates_v001.csv",
    "novegeo_beach_candidates_v001.csv",
    "novegeo_cliff_candidates_v001.csv",
)


def candidate_source_rows() -> tuple[tuple[Path, dict[str, str]], ...]:
    out: list[tuple[Path, dict[str, str]]] = []
    for name in _CANDIDATE_FILES:
        path = _CANDIDATE_ROOT / name
        out.extend((path, row) for row in csv_rows(path))
    return tuple(out)


@lru_cache(maxsize=1)
def candidate_row_by_id() -> dict[str, dict[str, str]]:
    return {row["candidate_id"]: row for _, row in candidate_source_rows()}


@lru_cache(maxsize=1)
def derive_occupancy_relationships() -> tuple[SpatialOccupancyRelationship, ...]:
    containment = {row.coordinate_candidate_id: row for row in derive_containment_qualifications()}
    out: list[SpatialOccupancyRelationship] = []

    for path, row in candidate_source_rows():
        candidate_id = row["candidate_id"]
        feature_type = row["feature_type"]
        if row.get("reference_longitude"):
            lon = Decimal(row["reference_longitude"])
            lat = Decimal(row["reference_latitude"])
            coordinate_id = candidate_identity(lon, lat)
            relation = containment.get(coordinate_id)
            if relation is None or relation.qualification_status != "PASS" or not relation.sovereign_part_id:
                raise ValueError(f"candidate {candidate_id} lacks qualified sovereign containment")
            out.append(SpatialOccupancyRelationship(
                relationship_evidence_id=stable_id("sprel:nngla:", candidate_id, coordinate_id, "WITHIN", relation.sovereign_part_id),
                subject_family="NATURAL_FEATURE",
                subject_type=feature_type,
                subject_id=candidate_id,
                subject_geometry_reference=row.get("source_reference_id", ""),
                relationship_type_code=RelationshipType.WITHIN,
                object_family="SOVEREIGN_GROUND",
                object_type="SOVEREIGN_PART",
                object_id=relation.sovereign_part_id,
                spatial_reference_id=coordinate_id,
                coordinate_candidate_id=coordinate_id,
                evidence_class="QUALIFIED_REFERENCE_POINT",
                evidence_reference=f"{path.relative_to(ROOT).as_posix()}#{candidate_id}",
                relationship_basis="BUNDLE17B_ACTUAL_BOUNDARY_CONTAINMENT_AT_QUALIFIED_REFERENCE_POINT",
                distance_value="",
                distance_unit="",
                valid_from="",
                valid_to="",
                qualification_status="PASS",
                runtime_effect_scope="SHARED_REFERENCE",
                notes="Reference-point occupancy does not assert the full physical feature extent.",
            ))
            continue

        if row.get("start_longitude"):
            for endpoint in ("start", "end"):
                lon = Decimal(row[f"{endpoint}_longitude"])
                lat = Decimal(row[f"{endpoint}_latitude"])
                coordinate_id = candidate_identity(lon, lat)
                relation = containment.get(coordinate_id)
                if relation is None or relation.qualification_status != "PASS" or relation.boundary_relation != "TOUCHES":
                    raise ValueError(f"coastal candidate {candidate_id} {endpoint} is not qualified boundary evidence")
                out.append(SpatialOccupancyRelationship(
                    relationship_evidence_id=stable_id("sprel:nngla:", candidate_id, endpoint.upper(), coordinate_id, "TOUCHES", "boundary:novegeo:sovereign"),
                    subject_family="NATURAL_FEATURE",
                    subject_type=feature_type,
                    subject_id=candidate_id,
                    subject_geometry_reference=f"{row.get('source_polygon_id','')}:{row.get('source_ring_id','')}:{row.get('start_vertex_sequence','')}-{row.get('end_vertex_sequence','')}",
                    relationship_type_code=RelationshipType.TOUCHES,
                    object_family="SOVEREIGN_GROUND",
                    object_type="SOVEREIGN_BOUNDARY",
                    object_id="boundary:novegeo:sovereign",
                    spatial_reference_id=coordinate_id,
                    coordinate_candidate_id=coordinate_id,
                    evidence_class=f"COASTAL_{endpoint.upper()}_BOUNDARY_EVIDENCE",
                    evidence_reference=f"{path.relative_to(ROOT).as_posix()}#{candidate_id}:{endpoint.upper()}",
                    relationship_basis="BUNDLE17B_ACTUAL_BOUNDARY_RELATION_AT_SOURCE_RESERVED_COASTAL_ENDPOINT",
                    distance_value="",
                    distance_unit="",
                    valid_from="",
                    valid_to="",
                    qualification_status="PASS",
                    runtime_effect_scope="SHARED_REFERENCE",
                    notes="Boundary endpoint is real evidence; reserved coastal sector is not yet a completed physical feature geometry.",
                ))
    ids = [row.relationship_evidence_id for row in out]
    if len(ids) != len(set(ids)):
        raise ValueError("spatial occupancy relationship identity collision")
    return tuple(out)


__all__ = ["candidate_source_rows", "candidate_row_by_id", "derive_occupancy_relationships"]
