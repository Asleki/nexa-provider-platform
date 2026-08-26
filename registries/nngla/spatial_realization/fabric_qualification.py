"""Read-only qualification for Delivery-1 shared-face candidate fabrics."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping

from .contracts import ParentFabricScope
from .face_assignment import FabricAssignmentResult
from .face_polygonization import FabricFaceSet
from .source import administrative_geometry_payload


@dataclass(frozen=True, slots=True)
class PrototypeFabricQualification:
    scope_fingerprint: str
    assignment_sha256: str
    qualification_sha256: str
    status: str
    valid_subject_ids: tuple[str, ...]
    invalid_subject_ids: tuple[str, ...]
    face_exclusivity: bool
    complete_sibling_set: bool
    shared_face_identity_by_construction: bool
    candidate_gap_km2: float
    candidate_outside_parent_km2: float
    union_outside_parent_diagnostic_km2: float
    candidate_positive_overlap_km2: float
    parent_area_km2: float
    candidate_area_sum_km2: float
    area_conservation_delta_km2: float

    @property
    def prototype_ready(self) -> bool:
        return self.status == "PROTOTYPE_READY_FOR_POSTGIS_EXACT_VALIDATION"


@dataclass(frozen=True, slots=True)
class PostGISExactQualification:
    valid_all: bool
    every_child_covered_by_parent: bool
    union_covered_by_parent: bool
    parent_covered_by_union: bool
    symmetric_difference_m2: float
    positive_overlap_m2: float

    @property
    def exact_pass(self) -> bool:
        return (
            self.valid_all
            and self.every_child_covered_by_parent
            and self.union_covered_by_parent
            and self.parent_covered_by_union
            and self.symmetric_difference_m2 == 0.0
            and self.positive_overlap_m2 == 0.0
        )


def _projected_area_km2(geometry) -> float:
    from pyproj import Transformer
    from shapely.ops import transform
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    return float(transform(transformer.transform, geometry).area) / 1_000_000.0


def _parent_geometry(scope: ParentFabricScope, overrides: Mapping[str, object] | None):
    if overrides and scope.parent.subject_id in overrides:
        return overrides[scope.parent.subject_id]
    from shapely import from_geojson
    return from_geojson(administrative_geometry_payload(scope.parent.subject_id))


def qualify_candidate_fabric(
    scope: ParentFabricScope,
    face_set: FabricFaceSet,
    assignment: FabricAssignmentResult,
    *,
    geometry_overrides: Mapping[str, object] | None = None,
) -> PrototypeFabricQualification:
    """Prove read-only face accounting before asking PostGIS for exact predicates.

    This is intentionally not a legalization/authority qualification.  It proves
    that the candidate is complete, face-exclusive and free of positive-area
    gap/outside/overlap under the local reference engine, then labels the result
    ready for independent PostGIS exact validation.
    """
    if assignment.scope_fingerprint != scope.fingerprint or face_set.scope_fingerprint != scope.fingerprint:
        raise ValueError("fabric qualification scope mismatch")
    if assignment.face_set_sha256 != face_set.face_set_sha256:
        raise ValueError("fabric qualification face-set mismatch")

    from shapely import from_wkb
    from shapely.ops import unary_union

    candidate_by_subject = assignment.candidate_by_subject
    expected_ids = tuple(sorted(item.subject_id for item in scope.exhaustive_siblings))
    complete = tuple(sorted(candidate_by_subject)) == expected_ids
    geometries = {
        subject_id: from_wkb(bytes.fromhex(candidate_by_subject[subject_id].geometry_wkb_hex))
        for subject_id in expected_ids
        if subject_id in candidate_by_subject
    }
    valid_ids = tuple(sorted(subject_id for subject_id, geometry in geometries.items() if geometry.is_valid and not geometry.is_empty))
    invalid_ids = tuple(sorted(set(expected_ids) - set(valid_ids)))

    face_ids = [item.face_id for item in assignment.assigned_faces]
    expected_face_ids = [item.face_id for item in face_set.faces]
    face_exclusive = len(face_ids) == len(set(face_ids)) and set(face_ids) == set(expected_face_ids)
    assigned_face_refs = [face_id for candidate in assignment.sibling_candidates for face_id in candidate.assigned_face_ids]
    shared_by_construction = (
        len(assigned_face_refs) == len(set(assigned_face_refs))
        and set(assigned_face_refs) == set(expected_face_ids)
        and face_exclusive
    )

    parent = _parent_geometry(scope, geometry_overrides)
    union = unary_union(list(geometries.values())) if geometries else parent.__class__()
    gap = _projected_area_km2(parent.difference(union))
    union_outside = _projected_area_km2(union.difference(parent))
    outside = sum(_projected_area_km2(geometry.difference(parent)) for geometry in geometries.values())
    overlap = 0.0
    ordered_geometries = [(subject_id, geometries[subject_id]) for subject_id in expected_ids if subject_id in geometries]
    for index, (_, left) in enumerate(ordered_geometries):
        for _, right in ordered_geometries[index + 1:]:
            intersection = left.intersection(right)
            if not intersection.is_empty:
                overlap += _projected_area_km2(intersection)

    parent_area = _projected_area_km2(parent)
    candidate_area_sum = sum(_projected_area_km2(geometry) for geometry in geometries.values())
    area_delta = candidate_area_sum - parent_area
    ready = (
        complete
        and not invalid_ids
        and face_exclusive
        and shared_by_construction
        and gap == 0.0
        and outside == 0.0
        and overlap == 0.0
    )
    status = "PROTOTYPE_READY_FOR_POSTGIS_EXACT_VALIDATION" if ready else "PROTOTYPE_BLOCKED"
    material = {
        "scope": scope.fingerprint,
        "face_set": face_set.face_set_sha256,
        "assignment": assignment.assignment_sha256,
        "status": status,
        "valid": valid_ids,
        "invalid": invalid_ids,
        "face_exclusive": face_exclusive,
        "complete": complete,
        "shared": shared_by_construction,
        "gap_km2": gap,
        "outside_km2": outside,
        "union_outside_diagnostic_km2": union_outside,
        "overlap_km2": overlap,
        "parent_area_km2": parent_area,
        "candidate_area_sum_km2": candidate_area_sum,
    }
    qualification_sha = sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return PrototypeFabricQualification(
        scope_fingerprint=scope.fingerprint,
        assignment_sha256=assignment.assignment_sha256,
        qualification_sha256=qualification_sha,
        status=status,
        valid_subject_ids=valid_ids,
        invalid_subject_ids=invalid_ids,
        face_exclusivity=face_exclusive,
        complete_sibling_set=complete,
        shared_face_identity_by_construction=shared_by_construction,
        candidate_gap_km2=gap,
        candidate_outside_parent_km2=outside,
        union_outside_parent_diagnostic_km2=union_outside,
        candidate_positive_overlap_km2=overlap,
        parent_area_km2=parent_area,
        candidate_area_sum_km2=candidate_area_sum,
        area_conservation_delta_km2=area_delta,
    )


def qualify_candidate_fabric_postgis(
    connection,
    scope: ParentFabricScope,
    assignment: FabricAssignmentResult,
    *,
    geometry_overrides: Mapping[str, object] | None = None,
) -> PostGISExactQualification:
    """Run exact PostGIS predicates against in-memory candidate WKB only.

    The SQL is SELECT-only: it does not query or mutate canonical NNGLA tables.
    """
    from shapely import to_wkb
    parent = _parent_geometry(scope, geometry_overrides)
    parent_hex = to_wkb(parent, hex=True, byte_order=1)
    candidates = tuple(sorted(assignment.sibling_candidates, key=lambda item: item.subject_id))
    if not candidates:
        raise ValueError("PostGIS qualification requires sibling candidates")
    values_sql = ",".join(["(%s,%s)"] * len(candidates))
    params = []
    for item in candidates:
        params.extend((item.subject_id, item.geometry_wkb_hex))
    sql = f"""
    WITH parent AS (
      SELECT ST_GeomFromEWKB(decode(%s,'hex')) AS geom
    ), raw(subject_id,payload) AS (VALUES {values_sql}),
    siblings AS (
      SELECT subject_id,ST_GeomFromEWKB(decode(payload,'hex')) AS geom FROM raw
    ), u AS (
      SELECT ST_UnaryUnion(ST_Collect(geom ORDER BY subject_id)) AS geom FROM siblings
    ), pair_overlaps AS (
      SELECT ST_Intersection(a.geom,b.geom) AS geom
      FROM siblings a JOIN siblings b ON a.subject_id < b.subject_id
    )
    SELECT
      (SELECT COALESCE(bool_and(ST_IsValid(geom)),false) FROM siblings),
      (SELECT COALESCE(bool_and(ST_Covers(parent.geom,siblings.geom)),false) FROM siblings CROSS JOIN parent),
      ST_Covers(parent.geom,u.geom),
      ST_Covers(u.geom,parent.geom),
      ST_Area(ST_SymDifference(parent.geom,u.geom)::geography),
      COALESCE((SELECT SUM(ST_Area(geom::geography)) FROM pair_overlaps WHERE NOT ST_IsEmpty(geom) AND ST_Dimension(geom)=2),0)
    FROM parent CROSS JOIN u
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, (parent_hex,) + tuple(params))
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("PostGIS exact fabric qualification returned no result")
    return PostGISExactQualification(
        valid_all=bool(row[0]),
        every_child_covered_by_parent=bool(row[1]),
        union_covered_by_parent=bool(row[2]),
        parent_covered_by_union=bool(row[3]),
        symmetric_difference_m2=float(row[4] or 0.0),
        positive_overlap_m2=float(row[5] or 0.0),
    )


__all__ = [
    "PrototypeFabricQualification",
    "PostGISExactQualification",
    "qualify_candidate_fabric",
    "qualify_candidate_fabric_postgis",
]
