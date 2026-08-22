"""Governed all-or-nothing execution for P006.7.11.10 place spatialization."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json

from ._shared import (
    BUNDLE_CODE,
    BUNDLE_EFFECTIVE_DATE,
    INPUT_PATHS,
    ROOT,
    SOURCE_REPOSITORY_REVISION,
    payload_sha256,
    sha256_path,
    stable_id,
)
from .contracts import GeometryRole, PlaceSpatialExecutionReceipt
from .footprints import derive_point_only_exceptions, derive_settlement_footprints
from .persistence import footprint_geojson, point_geojson
from .qualification import bundle19a_is_qualified, qualification_findings
from .relationships import derive_place_spatial_relationships
from .siting import derive_place_reference_points


def bundle_source_hashes() -> tuple[tuple[str, str], ...]:
    """Return deterministic file hashes for all locked inputs and Bundle 19A policies."""
    return tuple((path.relative_to(ROOT).as_posix(), sha256_path(path)) for path in INPUT_PATHS)


def bundle_fingerprint() -> str:
    """Fingerprint the exact qualified spatial plan, policy inputs and repository revision."""
    points = derive_place_reference_points()
    footprints = derive_settlement_footprints()
    exceptions = derive_point_only_exceptions()
    relationships = derive_place_spatial_relationships()
    payload = {
        "bundle_code": BUNDLE_CODE,
        "effective_date": BUNDLE_EFFECTIVE_DATE,
        "repository_revision": SOURCE_REPOSITORY_REVISION,
        "source_hashes": bundle_source_hashes(),
        "place_reference_points": [asdict(row) for row in points],
        "settlement_footprints": [asdict(row) for row in footprints],
        "point_only_exceptions": [asdict(row) for row in exceptions],
        "parent_spatial_evidence": [asdict(row) for row in relationships],
    }
    return payload_sha256(payload)


def _execution_id(fingerprint: str) -> str:
    return f"nnglarun:place-spatial:{fingerprint[:32]}"


def execute_place_spatialization(
    repository,
    *,
    submitter_actor_id: str,
    approver_actor_id: str,
) -> PlaceSpatialExecutionReceipt:
    """Apply exactly one qualified Bundle 19A spatialization to a repository.

    All geometry payloads are qualified before the first identity allocation.  The actual
    allocator + inserts + place associations + execution receipt then occur in one transaction.
    """
    submitter = str(submitter_actor_id).strip()
    approver = str(approver_actor_id).strip()
    if not submitter or not approver:
        raise ValueError("submitter_actor_id and approver_actor_id are required")
    if submitter == approver:
        raise ValueError("submitter and approver must remain separate")

    findings = qualification_findings()
    if findings:
        raise RuntimeError("Bundle 19A qualification failed: " + ",".join(findings))

    fingerprint = bundle_fingerprint()
    replay = repository.replay(fingerprint)
    if replay is not None:
        return replay

    repository.preflight()
    points = derive_place_reference_points()
    footprints = derive_settlement_footprints()
    exceptions = {row.place_id: row for row in derive_point_only_exceptions()}
    footprint_by_place = {row.place_id: row for row in footprints}

    # Critical gate: PostGIS/static qualification occurs before any NG-GEO number is consumed.
    for point in points:
        repository.qualify_geometry(point.place_id, GeometryRole.PLACE_REFERENCE_POINT, point_geojson(point))
        footprint = footprint_by_place.get(point.place_id)
        if footprint is not None:
            repository.qualify_geometry(point.place_id, GeometryRole.SETTLEMENT_FOOTPRINT, footprint_geojson(footprint))

    execution_id = _execution_id(fingerprint)
    item_details: list[dict[str, object]] = []
    with repository.transaction():
        for point in points:
            point_payload = point_geojson(point)
            point_geometry_id = repository.reserve_geometry(
                point.place_id, GeometryRole.PLACE_REFERENCE_POINT, point.geometry_reservation_key
            )
            repository.persist_geometry(
                geometry_id=point_geometry_id,
                subject_id=point.place_id,
                role=GeometryRole.PLACE_REFERENCE_POINT,
                payload=point_payload,
                source_candidate_id=point.reference_candidate_id,
            )

            footprint_geometry_id = ""
            footprint = footprint_by_place.get(point.place_id)
            if footprint is not None:
                footprint_payload = footprint_geojson(footprint)
                footprint_geometry_id = repository.reserve_geometry(
                    point.place_id, GeometryRole.SETTLEMENT_FOOTPRINT, footprint.geometry_reservation_key
                )
                repository.persist_geometry(
                    geometry_id=footprint_geometry_id,
                    subject_id=point.place_id,
                    role=GeometryRole.SETTLEMENT_FOOTPRINT,
                    payload=footprint_payload,
                    source_candidate_id=footprint.footprint_candidate_id,
                )

            repository.associate_place_reference(
                place_id=point.place_id,
                source_place_code=point.source_place_code,
                geometry_id=point_geometry_id,
            )
            exception = exceptions.get(point.place_id)
            item_details.append({
                "source_place_code": point.source_place_code,
                "place_id": point.place_id,
                "place_type_code": point.place_type_code,
                "region_code": point.region_code,
                "point_geometry_id": point_geometry_id,
                "footprint_geometry_id": footprint_geometry_id,
                "point_only_reason": exception.reason_code if exception else "",
                "reference_candidate_id": point.reference_candidate_id,
                "supporting_spatial_point_id": point.supporting_spatial_point_id,
                "runtime_effect_scope": point.runtime_effect_scope,
                "publication_ready": False,
            })

        receipt = PlaceSpatialExecutionReceipt(
            execution_id=execution_id,
            fingerprint_sha256=fingerprint,
            database_name=repository.database_name,
            environment_name=repository.environment_name,
            repository_revision=SOURCE_REPOSITORY_REVISION,
            submitter_actor_id=submitter,
            approver_actor_id=approver,
            selected_place_count=len(points),
            associated_place_count=len(points),
            geometry_insert_count=len(points) + len(footprints),
            footprint_insert_count=len(footprints),
            point_only_count=len(exceptions),
            status="APPLIED",
            replayed=False,
        )
        repository.persist_execution_receipt(receipt, item_details=tuple(item_details))
    return receipt


__all__ = ["bundle_source_hashes", "bundle_fingerprint", "execute_place_spatialization"]
