"""Bundle 17F closure qualification."""
from __future__ import annotations
from collections import Counter

from registries.nngla.spatial_fabric.bundle17e import bundle17e_is_qualified
from ._shared import LOCKED_CANONICAL_COUNTS
from .associations import derive_subject_spatial_association_candidates
from .canonical_alignment import alignment_counts, derive_existing_canonical_alignment, remaining_noncanonical_road_candidate_ids
from .contracts import AssociationStatus
from .preconditions import derive_spatial_association_precondition_results
from .traversal import derive_geometry_traversal_qualifications


def bundle17f_findings() -> tuple[str, ...]:
    findings = []
    if alignment_counts() != LOCKED_CANONICAL_COUNTS:
        findings.append("LOCKED_CANONICAL_COUNT_DRIFT")
    if len(derive_existing_canonical_alignment()) != 1284:
        findings.append("ALIGNMENT_TOTAL_NOT_1284")
    remaining = remaining_noncanonical_road_candidate_ids()
    if len(remaining) != 550 or remaining[0] != "NG-RD-CAND-000351" or remaining[-1] != "NG-RD-CAND-000900":
        findings.append("NONCANONICAL_ROAD_GUARD_FAILED")
    traversal = derive_geometry_traversal_qualifications()
    if len(traversal) != 21 or any(row.traversal_status != "PASS" for row in traversal):
        findings.append("EXISTING_GEOMETRY_TRAVERSAL_NOT_FULLY_QUALIFIED")
    associations = derive_subject_spatial_association_candidates()
    counts = Counter(row.association_status for row in associations)
    if counts[AssociationStatus.READY_ASSOCIATE_EXISTING_GEOMETRY] != 20:
        findings.append("DIRECT_FEATURE_GEOMETRY_ASSOCIATION_COUNT_NOT_20")
    if counts[AssociationStatus.SUBJECT_ROLE_RECONCILIATION_REQUIRED] != 1:
        findings.append("MAINLAND_COUNTRY_SUBJECT_GUARD_MISSING")
    if counts[AssociationStatus.DEFERRED_NO_GEOMETRY] != 1242:
        findings.append("DEFERRED_GEOMETRY_COUNT_NOT_1242")
    pre = derive_spatial_association_precondition_results()
    if any(row.precondition_status == "FAIL" for row in pre):
        findings.append("ASSOCIATION_PRECONDITION_FAILURE")
    return tuple(findings)


def bundle17f_is_qualified() -> bool:
    return bundle17e_is_qualified() and not bundle17f_findings()


__all__ = ["bundle17f_findings", "bundle17f_is_qualified"]
