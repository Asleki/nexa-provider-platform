"""Bundle 17F fail-closed spatial association precondition evaluation."""
from __future__ import annotations
from functools import lru_cache

from .associations import derive_subject_spatial_association_candidates
from .contracts import AssociationStatus, SpatialAssociationPreconditionResult
from .traversal import derive_geometry_traversal_qualifications


@lru_cache(maxsize=1)
def derive_spatial_association_precondition_results() -> tuple[SpatialAssociationPreconditionResult, ...]:
    traversal = {row.geometry_id: row for row in derive_geometry_traversal_qualifications()}
    out = []
    for index, association in enumerate(derive_subject_spatial_association_candidates(), start=1):
        identity_ok = bool(association.canonical_subject_id)
        geometry_available = bool(association.geometry_id)
        traversal_ok = bool(geometry_available and traversal.get(association.geometry_id) and traversal[association.geometry_id].traversal_status == "PASS")
        role_ok = association.association_status is not AssociationStatus.SUBJECT_ROLE_RECONCILIATION_REQUIRED
        if association.association_status is AssociationStatus.READY_ASSOCIATE_EXISTING_GEOMETRY:
            ready = identity_ok and geometry_available and traversal_ok and role_ok
            status = "PASS_READY_TO_ASSOCIATE" if ready else "FAIL"
            findings = "" if ready else "READY_ASSOCIATION_PRECONDITION_FAILED"
        elif association.association_status is AssociationStatus.DEFERRED_NO_GEOMETRY:
            ready = False
            status = "DEFERRED_NO_GEOMETRY"
            findings = "GOVERNED_GEOMETRY_REQUIRED_BEFORE_ASSOCIATION"
        elif association.association_status is AssociationStatus.SUBJECT_ROLE_RECONCILIATION_REQUIRED:
            ready = False
            status = "DEFERRED_SUBJECT_ROLE_RECONCILIATION"
            findings = "MAINLAND_FEATURE_MUST_NOT_BE_SILENTLY_EQUATED_WITH_COUNTRY_SOVEREIGN_BOUNDARY"
        else:
            ready = False
            status = "FAIL"
            findings = association.association_status.value
        out.append(SpatialAssociationPreconditionResult(
            precondition_result_id=f"NG-SPAPRE-{index:07d}", association_candidate_id=association.association_candidate_id,
            canonical_subject_id=association.canonical_subject_id, geometry_id=association.geometry_id,
            identity_preserved=identity_ok, canonical_subject_confirmed=identity_ok,
            geometry_evidence_available=geometry_available, geometry_traversal_valid=traversal_ok,
            subject_role_compatible=role_ok, association_ready=ready, precondition_status=status, findings=findings,
        ))
    return tuple(out)


__all__ = ["derive_spatial_association_precondition_results"]
