"""Independent Delivery-2 qualification bound to one immutable candidate package."""
from __future__ import annotations

from .contracts import CandidateLifecycleStatus, CandidatePackage, CandidateQualificationDecision
from .fingerprints import digest, stable_id
from ..fabric_qualification import qualify_candidate_fabric, qualify_candidate_fabric_postgis
from ..shared_face_preview import SharedFacePrototypePreview


class CandidateQualificationError(RuntimeError):
    pass


class CandidateStaleError(CandidateQualificationError):
    """Raised when a recursive candidate no longer matches its qualified parent."""


def _verify_recursive_parent_binding(
    package: CandidatePackage,
    preview: SharedFacePrototypePreview,
    *,
    qualified_parent_candidate_id: str,
    qualified_parent_candidate_geometry_sha256: str,
) -> None:
    if not package.parent_candidate_id:
        if qualified_parent_candidate_id or qualified_parent_candidate_geometry_sha256:
            raise CandidateQualificationError("non-recursive candidate cannot accept a qualified-parent binding")
        return
    if not qualified_parent_candidate_id or not qualified_parent_candidate_geometry_sha256:
        raise CandidateStaleError("recursive candidate qualification requires the current qualified parent candidate")
    if (
        qualified_parent_candidate_id != package.parent_candidate_id
        or qualified_parent_candidate_geometry_sha256 != package.parent_candidate_geometry_sha256
    ):
        raise CandidateStaleError("recursive candidate is stale relative to the current qualified parent candidate")
    scope_parent = preview.scope.parent
    if (
        scope_parent.source_candidate_id != package.parent_candidate_id
        or scope_parent.geometry_checksum_sha256 != package.parent_candidate_geometry_sha256
    ):
        raise CandidateStaleError("recursive preview parent binding no longer matches the candidate package")


def qualify_package(
    package: CandidatePackage,
    preview: SharedFacePrototypePreview,
    *,
    qualifier_actor_id: str,
    connection=None,
    qualified_parent_candidate_id: str = "",
    qualified_parent_candidate_geometry_sha256: str = "",
    geometry_overrides=None,
) -> CandidateQualificationDecision:
    if qualifier_actor_id == package.author_actor_id:
        raise CandidateQualificationError("candidate author cannot independently qualify own package")
    if package.lifecycle_status is not CandidateLifecycleStatus.READY_FOR_CANDIDATE_QUALIFICATION:
        raise CandidateQualificationError("candidate package is not ready for independent qualification")
    if preview.assignment is None or preview.qualification is None:
        raise CandidateQualificationError("qualification requires assigned Delivery-1 candidate fabric")
    _verify_recursive_parent_binding(
        package,
        preview,
        qualified_parent_candidate_id=qualified_parent_candidate_id,
        qualified_parent_candidate_geometry_sha256=qualified_parent_candidate_geometry_sha256,
    )
    if package.scope_fingerprint != preview.scope.fingerprint or package.face_set_sha256 != preview.face_set.face_set_sha256:
        raise CandidateQualificationError("candidate package is stale relative to supplied preview")
    if package.assignment_sha256 != preview.assignment.assignment_sha256:
        raise CandidateQualificationError("candidate assignment digest mismatch")
    local = qualify_candidate_fabric(preview.scope, preview.face_set, preview.assignment, geometry_overrides=geometry_overrides)
    if local.qualification_sha256 != package.qualification_sha256:
        raise CandidateQualificationError("candidate qualification digest mismatch")
    if connection is None:
        valid_all = not local.invalid_subject_ids
        child_cover = local.candidate_outside_parent_km2 == 0.0
        union_cover = local.candidate_outside_parent_km2 == 0.0
        parent_cover = local.candidate_gap_km2 == 0.0
        symdiff = (local.candidate_gap_km2 + local.union_outside_parent_diagnostic_km2) * 1_000_000.0
        overlap = local.candidate_positive_overlap_km2 * 1_000_000.0
        exact_pass = local.prototype_ready and symdiff == 0.0 and overlap == 0.0
    else:
        exact = qualify_candidate_fabric_postgis(connection, preview.scope, preview.assignment, geometry_overrides=geometry_overrides)
        valid_all, child_cover, union_cover, parent_cover = (
            exact.valid_all, exact.every_child_covered_by_parent, exact.union_covered_by_parent, exact.parent_covered_by_union
        )
        symdiff, overlap, exact_pass = exact.symmetric_difference_m2, exact.positive_overlap_m2, exact.exact_pass
    status = CandidateLifecycleStatus.CANDIDATE_QUALIFIED if exact_pass else CandidateLifecycleStatus.CANDIDATE_REJECTED
    material = {
        "run": package.fabric_run_id, "package": package.package_sha256, "qualifier": qualifier_actor_id,
        "status": status.value, "valid": valid_all, "childCover": child_cover, "unionCover": union_cover,
        "parentCover": parent_cover, "symdiff": symdiff, "overlap": overlap,
    }
    return CandidateQualificationDecision(
        qualification_id=stable_id("fabric-qualification:nngla:", material),
        fabric_run_id=package.fabric_run_id, package_sha256=package.package_sha256,
        qualifier_actor_id=qualifier_actor_id, status=status, valid_all=valid_all,
        every_child_covered_by_parent=child_cover, union_covered_by_parent=union_cover,
        parent_covered_by_union=parent_cover, symmetric_difference_m2=float(symdiff),
        positive_overlap_m2=float(overlap), decision_sha256=digest(material),
    )


__all__ = ["CandidateQualificationError", "CandidateStaleError", "qualify_package"]
