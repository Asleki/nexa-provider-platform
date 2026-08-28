"""Separate child-fabric completeness reporting for Delivery 3 R1."""
from __future__ import annotations

from .contracts import FabricCompleteness, FabricCompletenessStatus, stable_digest


def completeness_report(
    *, parent_administrative_area_id: str, expected_child_count: int,
    qualified_child_count: int, published_child_count: int,
    gap_m2: float, positive_overlap_m2: float, evidence_material: object,
) -> FabricCompleteness:
    if expected_child_count == 0:
        status = FabricCompletenessStatus.NOT_ASSESSED
    elif (
        qualified_child_count == expected_child_count
        and float(gap_m2) == 0.0
        and float(positive_overlap_m2) == 0.0
    ):
        status = FabricCompletenessStatus.COMPLETE
    else:
        status = FabricCompletenessStatus.PARTIAL
    return FabricCompleteness(
        parent_administrative_area_id=parent_administrative_area_id,
        status=status,
        expected_child_count=expected_child_count,
        qualified_child_count=qualified_child_count,
        published_child_count=published_child_count,
        gap_m2=float(gap_m2),
        positive_overlap_m2=float(positive_overlap_m2),
        evidence_sha256=stable_digest(evidence_material),
    )


__all__ = ["completeness_report"]
