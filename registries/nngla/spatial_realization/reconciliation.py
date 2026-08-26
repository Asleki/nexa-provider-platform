"""Selection-scoped live target reconciliation for spatial realization."""
from __future__ import annotations

from .contracts import (
    CityClosure,
    GeometryCandidate,
    GeometryRole,
    ReconciliationAction,
    ReconciliationItem,
    SubjectType,
    TargetGeometryState,
    TargetSnapshot,
    TopologyAssessment,
)


def _active_for(snapshot: TargetSnapshot, candidate: GeometryCandidate) -> tuple[TargetGeometryState, ...]:
    return tuple(
        row for row in snapshot.active_geometries.get(candidate.subject_id, ())
        if row.geometry_role == candidate.geometry_role.value
    )


def reconcile_candidate(candidate: GeometryCandidate, snapshot: TargetSnapshot) -> ReconciliationItem:
    active = _active_for(snapshot, candidate)
    if len(active) > 1:
        return ReconciliationItem(
            candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,
            candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,
            "MULTIPLE_ACTIVE_GEOMETRIES_FOR_SUBJECT_ROLE",
        )
    current = active[0] if active else None

    if candidate.subject_type is SubjectType.PLACE:
        place = snapshot.places.get(candidate.subject_id)
        if place is None:
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"CANONICAL_PLACE_MISSING")
        if candidate.geometry_role is GeometryRole.SETTLEMENT_FOOTPRINT:
            if current is None:
                return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.CREATE_NEW,"NO_ACTIVE_SETTLEMENT_FOOTPRINT")
            if current.checksum_sha256 == candidate.checksum_sha256:
                return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.REUSE_EXISTING,"EXACT_ACTIVE_SETTLEMENT_FOOTPRINT",current.geometry_id)
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"ACTIVE_SETTLEMENT_FOOTPRINT_DIFFERS_FROM_QUALIFIED_CANDIDATE",current.geometry_id)

        # Canonical place association always points to PLACE_REFERENCE_POINT only.
        if current is None:
            if place.geometry_reference is not None or place.spatial_assignment_status != "UNMAPPED_PENDING_ASSOCIATION":
                return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"PLACE_STATE_REFERENCES_MISSING_OR_UNEXPECTED_GEOMETRY")
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.CREATE_NEW,"NO_ACTIVE_PLACE_REFERENCE_POINT")
        if current.checksum_sha256 != candidate.checksum_sha256:
            if candidate.is_source_successor:
                return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.CREATE_SUCCESSOR,"APPROVED_SOURCE_SUCCESSOR_DIFFERS_FROM_ACTIVE_GEOMETRY",current.geometry_id)
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"ACTIVE_PLACE_REFERENCE_POINT_DIFFERS",current.geometry_id)
        if place.geometry_reference == current.geometry_id and place.spatial_assignment_status == "AUTHORITATIVE_GEOMETRY_ASSIGNED":
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.REUSE_EXISTING,"EXACT_PLACE_STATE_MATCH",current.geometry_id)
        if place.geometry_reference is None and place.spatial_assignment_status == "UNMAPPED_PENDING_ASSOCIATION":
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.ASSOCIATE_EXISTING,"EXACT_PLACE_GEOMETRY_EXISTS_ASSOCIATION_PENDING",current.geometry_id)
        return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"PLACE_ASSOCIATION_CONFLICT",current.geometry_id)

    admin = snapshot.admins.get(candidate.subject_id)
    if admin is None:
        return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"CANONICAL_ADMINISTRATIVE_AREA_MISSING")
    if current is None:
        if admin.geometry_reference is not None or admin.boundary_status != "BOUNDARY_PENDING_LEGALIZATION" or admin.lifecycle_status != "PROVISIONAL":
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"ADMIN_STATE_REFERENCES_MISSING_OR_UNEXPECTED_GEOMETRY")
        return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.CREATE_NEW,"NO_ACTIVE_ADMINISTRATIVE_BOUNDARY")
    if current.checksum_sha256 != candidate.checksum_sha256:
        if candidate.is_source_successor:
            return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.CREATE_SUCCESSOR,"APPROVED_SOURCE_SUCCESSOR_DIFFERS_FROM_ACTIVE_GEOMETRY",current.geometry_id)
        return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"ACTIVE_ADMINISTRATIVE_BOUNDARY_DIFFERS",current.geometry_id)
    if admin.geometry_reference == current.geometry_id and admin.boundary_status == "LEGALIZED" and admin.lifecycle_status == "ACTIVE":
        return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.REUSE_EXISTING,"EXACT_ADMINISTRATIVE_STATE_MATCH",current.geometry_id)
    if admin.geometry_reference is None and admin.boundary_status == "BOUNDARY_PENDING_LEGALIZATION" and admin.lifecycle_status == "PROVISIONAL":
        return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.ASSOCIATE_EXISTING,"EXACT_ADMIN_GEOMETRY_EXISTS_ASSOCIATION_PENDING",current.geometry_id)
    return ReconciliationItem(candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,"ADMIN_ASSOCIATION_CONFLICT",current.geometry_id)


def reconcile_assessment(closure: CityClosure, assessment: TopologyAssessment, snapshot: TargetSnapshot) -> tuple[ReconciliationItem, ...]:
    # A blocking geometry-derived finding prevents *all* mutable actions for the
    # selected root.  This keeps geometry IDs unconsumed until the whole root is
    # independently qualification-clean.
    if assessment.blocking_findings:
        reason = "TOPOLOGY_BLOCKED:" + ",".join(sorted({f.rule_code for f in assessment.blocking_findings}))
        return tuple(
            ReconciliationItem(
                candidate.root_place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,
                candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.BLOCKED,reason,
            )
            for candidate in assessment.candidates
        )
    return tuple(reconcile_candidate(candidate,snapshot) for candidate in assessment.candidates)


def reconcile_selection(closures: tuple[CityClosure, ...], assessments: tuple[TopologyAssessment, ...], snapshot: TargetSnapshot) -> tuple[ReconciliationItem, ...]:
    assessment_by_root={item.root_place_id:item for item in assessments}
    out=[]
    for closure in closures:
        assessment=assessment_by_root[closure.root.place_id]
        out.extend(reconcile_assessment(closure,assessment,snapshot))
        # Validation-only dependencies are represented in the plan explicitly,
        # but never become persistence actions in a city-root run.
        for candidate in (closure.validation_parent,)+closure.overlays+tuple(
            peer for peer in closure.regional_partition_peers if peer.subject_id!=closure.admin_root.subject_id
        ):
            out.append(ReconciliationItem(
                closure.root.place_id,candidate.subject_id,candidate.subject_type,candidate.geometry_role,
                candidate.checksum_sha256,candidate.source_candidate_id,ReconciliationAction.NO_CHANGE,"VALIDATION_CONTEXT_ONLY",
            ))
    return tuple(out)


__all__=["reconcile_candidate","reconcile_assessment","reconcile_selection"]
