"""Deterministically materialize the governed Bundle 19A data products."""
from __future__ import annotations

from csv import DictWriter
from dataclasses import asdict
import json
from pathlib import Path

from ._shared import (
    ASSIGNMENTS_PATH,
    BUNDLE_CODE,
    BUNDLE_EFFECTIVE_DATE,
    BUNDLE_NAME,
    BUNDLE_VERSION,
    CRS_CODE,
    EFFECT_SCOPE,
    EVIDENCE_ROOT,
    FOOTPRINTS_PATH,
    PLACE_DATASET_ID,
    PLACE_DATASET_VERSION,
    QUALIFICATION_RESULTS_PATH,
    QUALIFIED_ROOT,
    REFERENCE_POINTS_PATH,
    RELATIONSHIPS_PATH,
    RELATIONSHIP_ROOT,
    ROOT,
    RUNTIME_MODE,
    SOURCE_HASHES_PATH,
    SOURCE_REPOSITORY_REVISION,
    SUMMARY_PATH,
)
from .execution import bundle_fingerprint, bundle_source_hashes
from .footprints import derive_point_only_exceptions, derive_settlement_footprints
from .qualification import bundle19a_is_qualified, qualification_findings
from .relationships import derive_place_spatial_relationships
from .siting import derive_place_reference_points


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def materialize_bundle19a_artifacts() -> tuple[Path, ...]:
    findings = qualification_findings()
    if findings:
        raise RuntimeError("cannot materialize unqualified Bundle 19A: " + ",".join(findings))

    points = derive_place_reference_points()
    footprints = derive_settlement_footprints()
    exceptions = derive_point_only_exceptions()
    relationships = derive_place_spatial_relationships()
    footprint_by_place = {row.place_id: row for row in footprints}
    exception_by_place = {row.place_id: row for row in exceptions}
    relationship_by_child = {row.child_place_id: row for row in relationships}

    _write_csv(
        REFERENCE_POINTS_PATH,
        (
            "reference_candidate_id", "source_place_code", "place_id", "canonical_name", "place_type_code", "region_code",
            "parent_source_place_code", "longitude", "latitude", "crs_code", "sovereign_part_id", "supporting_spatial_point_id",
            "support_distance_m", "placement_basis", "geometry_role_code", "geometry_reservation_key", "geometry_id",
            "geometry_id_state", "spatial_assignment_status", "outcome_status", "exception_code", "runtime_mode",
            "runtime_effect_scope", "publication_status", "legal_boundary_status",
        ),
        (
            {
                "reference_candidate_id": row.reference_candidate_id,
                "source_place_code": row.source_place_code,
                "place_id": row.place_id,
                "canonical_name": row.canonical_name,
                "place_type_code": row.place_type_code,
                "region_code": row.region_code,
                "parent_source_place_code": row.parent_source_place_code,
                "longitude": f"{row.longitude:.9f}",
                "latitude": f"{row.latitude:.9f}",
                "crs_code": row.crs_code,
                "sovereign_part_id": row.sovereign_part_id,
                "supporting_spatial_point_id": row.supporting_spatial_point_id,
                "support_distance_m": f"{row.support_distance_m:.3f}",
                "placement_basis": row.placement_basis,
                "geometry_role_code": "PLACE_REFERENCE_POINT",
                "geometry_reservation_key": row.geometry_reservation_key,
                "geometry_id": "",
                "geometry_id_state": "PENDING_GOVERNED_LIVE_RESERVATION",
                "spatial_assignment_status": "QUALIFIED_PENDING_LIVE_ASSOCIATION",
                "outcome_status": row.outcome_status.value,
                "exception_code": row.exception_code,
                "runtime_mode": RUNTIME_MODE,
                "runtime_effect_scope": row.runtime_effect_scope,
                "publication_status": "NOT_PUBLISHED",
                "legal_boundary_status": "NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY",
            }
            for row in points
        ),
    )

    features = []
    for row in footprints:
        features.append({
            "type": "Feature",
            "id": row.footprint_candidate_id,
            "properties": {
                "source_place_code": row.source_place_code,
                "place_id": row.place_id,
                "canonical_name": row.canonical_name,
                "place_type_code": row.place_type_code,
                "region_code": row.region_code,
                "geometry_role_code": row.geometry_role_code.value,
                "geometry_type_code": row.geometry_type_code,
                "nominal_radius_km": row.nominal_radius_km,
                "realized_radius_km": row.realized_radius_km,
                "area_sq_km": row.area_sq_km,
                "crs_code": row.crs_code,
                "sovereign_part_id": row.sovereign_part_id,
                "geometry_reservation_key": row.geometry_reservation_key,
                "geometry_id": None,
                "geometry_id_state": "PENDING_GOVERNED_LIVE_RESERVATION",
                "qualification_status": row.qualification_status,
                "source_basis": row.source_basis,
                "runtime_mode": RUNTIME_MODE,
                "runtime_effect_scope": row.runtime_effect_scope,
                "publication_status": "NOT_PUBLISHED",
                "legal_boundary_status": "NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[round(lon, 9), round(lat, 9)] for lon, lat in row.ring]],
            },
        })
    FOOTPRINTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FOOTPRINTS_PATH.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    _write_csv(
        RELATIONSHIPS_PATH,
        (
            "relationship_evidence_id", "child_place_id", "child_source_place_code", "parent_place_id", "parent_source_place_code",
            "distance_m", "parent_footprint_relation", "relationship_basis", "qualification_status", "runtime_effect_scope",
            "legal_containment_asserted",
        ),
        (
            {
                "relationship_evidence_id": row.relationship_evidence_id,
                "child_place_id": row.child_place_id,
                "child_source_place_code": row.child_source_place_code,
                "parent_place_id": row.parent_place_id,
                "parent_source_place_code": row.parent_source_place_code,
                "distance_m": f"{row.distance_m:.3f}",
                "parent_footprint_relation": row.parent_footprint_relation,
                "relationship_basis": row.relationship_basis,
                "qualification_status": row.qualification_status,
                "runtime_effect_scope": row.runtime_effect_scope,
                "legal_containment_asserted": "false",
            }
            for row in relationships
        ),
    )

    assignment_rows = []
    for point in points:
        assignment_rows.append({
            "assignment_candidate_id": f"spatialassign:nngla:{point.reference_candidate_id.split(':')[-1]}",
            "subject_type": "PLACE",
            "subject_id": point.place_id,
            "source_place_code": point.source_place_code,
            "geometry_role_code": "PLACE_REFERENCE_POINT",
            "geometry_reservation_key": point.geometry_reservation_key,
            "geometry_id": "",
            "geometry_id_state": "PENDING_GOVERNED_LIVE_RESERVATION",
            "effective_from": BUNDLE_EFFECTIVE_DATE,
            "effective_to": "",
            "assignment_version": 1,
            "assignment_status": "QUALIFIED_PENDING_LIVE_ASSOCIATION",
            "runtime_mode": RUNTIME_MODE,
            "runtime_effect_scope": EFFECT_SCOPE,
            "publication_status": "NOT_PUBLISHED",
        })
        footprint = footprint_by_place.get(point.place_id)
        if footprint is not None:
            assignment_rows.append({
                "assignment_candidate_id": f"spatialassign:nngla:{footprint.footprint_candidate_id.split(':')[-1]}",
                "subject_type": "PLACE",
                "subject_id": point.place_id,
                "source_place_code": point.source_place_code,
                "geometry_role_code": "SETTLEMENT_FOOTPRINT",
                "geometry_reservation_key": footprint.geometry_reservation_key,
                "geometry_id": "",
                "geometry_id_state": "PENDING_GOVERNED_LIVE_RESERVATION",
                "effective_from": BUNDLE_EFFECTIVE_DATE,
                "effective_to": "",
                "assignment_version": 1,
                "assignment_status": "QUALIFIED_PENDING_LIVE_ASSOCIATION",
                "runtime_mode": RUNTIME_MODE,
                "runtime_effect_scope": EFFECT_SCOPE,
                "publication_status": "NOT_PUBLISHED",
            })
    _write_csv(
        ASSIGNMENTS_PATH,
        tuple(assignment_rows[0].keys()),
        assignment_rows,
    )

    qualification_rows = []
    for point in points:
        footprint = footprint_by_place.get(point.place_id)
        exception = exception_by_place.get(point.place_id)
        relation = relationship_by_child.get(point.place_id)
        qualification_rows.append({
            "source_place_code": point.source_place_code,
            "place_id": point.place_id,
            "place_type_code": point.place_type_code,
            "region_code": point.region_code,
            "reference_point_status": "PASS",
            "reference_sovereign_part_id": point.sovereign_part_id,
            "supporting_spatial_point_id": point.supporting_spatial_point_id,
            "footprint_status": "PASS" if footprint else "POINT_ONLY_EXPLICIT_EXCEPTION",
            "footprint_candidate_id": footprint.footprint_candidate_id if footprint else "",
            "point_only_reason": exception.reason_code if exception else "",
            "parent_spatial_evidence_status": "PASS" if relation else "NOT_APPLICABLE_ROOT",
            "parent_footprint_relation": relation.parent_footprint_relation if relation else "",
            "sovereign_containment_status": "PASS",
            "geometry_identity_separation_status": "PASS",
            "administrative_legal_boundary_status": "NOT_CREATED_BY_P006.7.11.10",
            "publication_status": "NOT_PUBLISHED",
            "overall_qualification_status": "PASS",
        })
    _write_csv(QUALIFICATION_RESULTS_PATH, tuple(qualification_rows[0].keys()), qualification_rows)

    source_rows = [
        {"path": path, "sha256": digest, "role": "LOCKED_INPUT_OR_BUNDLE19A_POLICY"}
        for path, digest in bundle_source_hashes()
    ]
    _write_csv(SOURCE_HASHES_PATH, ("path", "sha256", "role"), source_rows)

    summary = {
        "bundle_code": BUNDLE_CODE,
        "bundle_name": BUNDLE_NAME,
        "bundle_version": BUNDLE_VERSION,
        "effective_date": BUNDLE_EFFECTIVE_DATE,
        "source_repository_revision": SOURCE_REPOSITORY_REVISION,
        "fingerprint_sha256": bundle_fingerprint(),
        "runtime_mode": RUNTIME_MODE,
        "runtime_effect_scope": EFFECT_SCOPE,
        "crs_code": CRS_CODE,
        "source_dataset_id": PLACE_DATASET_ID,
        "source_dataset_version": PLACE_DATASET_VERSION,
        "counts": {
            "canonical_places": len(points),
            "place_reference_points": len(points),
            "settlement_footprints": len(footprints),
            "point_only_explicit_outcomes": len(exceptions),
            "parent_spatial_evidence": len(relationships),
            "qualified_geometry_assignment_candidates": len(assignment_rows),
        },
        "database_contract": {
            "new_schema_migration_required": False,
            "geometry_identity_allocation": "LIVE GOVERNED geography.nngla_reserve_geometry_id",
            "place_geometry_reference_meaning": "CURRENT PRIMARY PLACE_REFERENCE_POINT ONLY",
        },
        "safety_boundaries": [
            "PLACE IDENTITY IS NOT GEOMETRY IDENTITY",
            "SETTLEMENT_FOOTPRINT IS NOT AN ADMINISTRATIVE OR LEGAL BOUNDARY",
            "P006.7.11.10 DOES NOT LEGALIZE ADMINISTRATIVE AREAS",
            "MAPPED DOES NOT IMPLY PUBLICLY PUBLISHED",
            "FRONTEND COORDINATES ARE NOT AUTHORITATIVE",
        ],
        "qualification_status": "PASS",
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return (
        REFERENCE_POINTS_PATH,
        FOOTPRINTS_PATH,
        RELATIONSHIPS_PATH,
        ASSIGNMENTS_PATH,
        QUALIFICATION_RESULTS_PATH,
        SOURCE_HASHES_PATH,
        SUMMARY_PATH,
    )


__all__ = ["materialize_bundle19a_artifacts"]
