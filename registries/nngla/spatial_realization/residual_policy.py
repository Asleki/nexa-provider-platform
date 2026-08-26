"""Residual classification policy for P006.7.11.15.5 R3.

Raw topology predicates remain authoritative evidence.  This policy never turns
``false`` into ``true``; it only decides whether the measured residual is small
enough to permit a deterministic successor proposal, or must remain blocked for
governed structural review.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

MAX_AUTOMATIC_RESIDUAL_KM2 = 0.01
MAX_AUTOMATIC_RESIDUAL_RATIO = 1e-6


class ResidualClass(str, Enum):
    NONE = "NONE"
    ZERO_AREA_BOUNDARY_RESIDUAL = "ZERO_AREA_BOUNDARY_RESIDUAL"
    MICRO_BOUNDARY_RESIDUAL = "MICRO_BOUNDARY_RESIDUAL"
    MATERIAL_TOPOLOGY_FAILURE = "MATERIAL_TOPOLOGY_FAILURE"


class RepairEligibility(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    AUTOMATIC_SUCCESSOR_ELIGIBLE = "AUTOMATIC_SUCCESSOR_ELIGIBLE"
    GOVERNED_STRUCTURAL_REVIEW_REQUIRED = "GOVERNED_STRUCTURAL_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class ResidualDecision:
    residual_class: ResidualClass
    repair_eligibility: RepairEligibility


def classify_residual(*, area_km2: float, area_ratio: float, difference_dimension: int | None) -> ResidualClass:
    area = max(float(area_km2 or 0.0), 0.0)
    ratio = max(float(area_ratio or 0.0), 0.0)
    if difference_dimension is not None and int(difference_dimension) < 2:
        return ResidualClass.ZERO_AREA_BOUNDARY_RESIDUAL
    if area == 0.0:
        return ResidualClass.ZERO_AREA_BOUNDARY_RESIDUAL
    if area <= MAX_AUTOMATIC_RESIDUAL_KM2 and ratio <= MAX_AUTOMATIC_RESIDUAL_RATIO:
        return ResidualClass.MICRO_BOUNDARY_RESIDUAL
    return ResidualClass.MATERIAL_TOPOLOGY_FAILURE


def executable_decision(*, area_km2: float, area_ratio: float, difference_dimension: int | None) -> ResidualDecision:
    residual = classify_residual(
        area_km2=area_km2,
        area_ratio=area_ratio,
        difference_dimension=difference_dimension,
    )
    if residual in {ResidualClass.ZERO_AREA_BOUNDARY_RESIDUAL, ResidualClass.MICRO_BOUNDARY_RESIDUAL}:
        eligibility = RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE
    else:
        eligibility = RepairEligibility.GOVERNED_STRUCTURAL_REVIEW_REQUIRED
    return ResidualDecision(residual, eligibility)


def context_decision(*, area_km2: float, area_ratio: float, difference_dimension: int | None) -> ResidualDecision:
    return ResidualDecision(
        classify_residual(
            area_km2=area_km2,
            area_ratio=area_ratio,
            difference_dimension=difference_dimension,
        ),
        RepairEligibility.CONTEXT_ONLY,
    )


@dataclass(frozen=True, slots=True)
class MicroAssignmentEvidence:
    effective_width_m: float | None
    unique_adjacency: bool
    lineage_complete: bool
    protected_edge_conflict: bool
    governed_max_width_m: float | None


def delivery1_micro_assignment_eligible(
    *,
    area_km2: float,
    area_ratio: float,
    difference_dimension: int | None,
    evidence: MicroAssignmentEvidence,
) -> bool:
    """Additional Delivery-1 gate for any future automatic seam assignment.

    R3's area+ratio thresholds remain necessary but are deliberately no longer
    sufficient.  No production width threshold is invented here; until an
    explicitly governed maximum width is supplied, the answer is fail-closed.
    """
    residual = classify_residual(
        area_km2=area_km2,
        area_ratio=area_ratio,
        difference_dimension=difference_dimension,
    )
    if residual not in {ResidualClass.ZERO_AREA_BOUNDARY_RESIDUAL, ResidualClass.MICRO_BOUNDARY_RESIDUAL}:
        return False
    if evidence.governed_max_width_m is None or float(evidence.governed_max_width_m) <= 0:
        return False
    if evidence.effective_width_m is None or float(evidence.effective_width_m) > float(evidence.governed_max_width_m):
        return False
    return bool(evidence.unique_adjacency and evidence.lineage_complete and not evidence.protected_edge_conflict)


__all__ = [
    "MAX_AUTOMATIC_RESIDUAL_KM2",
    "MAX_AUTOMATIC_RESIDUAL_RATIO",
    "ResidualClass",
    "RepairEligibility",
    "ResidualDecision",
    "MicroAssignmentEvidence",
    "delivery1_micro_assignment_eligible",
    "classify_residual",
    "executable_decision",
    "context_decision",
]
