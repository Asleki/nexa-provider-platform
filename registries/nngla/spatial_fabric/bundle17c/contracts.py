"""P006.7.11.7 Bundle 17C occupancy, compatibility and conflict contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class RelationshipType(str, Enum):
    CONTAINS = "CONTAINS"
    WITHIN = "WITHIN"
    INTERSECTS = "INTERSECTS"
    CROSSES = "CROSSES"
    TOUCHES = "TOUCHES"
    OVERLAPS = "OVERLAPS"
    ADJACENT_TO = "ADJACENT_TO"
    NEAR = "NEAR"
    FRONTS = "FRONTS"
    CONNECTED_TO = "CONNECTED_TO"


class CompatibilityOutcome(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_CONDITION = "ALLOW_WITH_CONDITION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCK = "BLOCK"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class ConflictStatus(str, Enum):
    NO_CONFLICT_AT_QUALIFIED_REFERENCE = "NO_CONFLICT_AT_QUALIFIED_REFERENCE"
    CONDITION_REQUIRED = "CONDITION_REQUIRED"
    CONFLICT = "CONFLICT"
    NOT_EVALUABLE_PENDING_GEOMETRY = "NOT_EVALUABLE_PENDING_GEOMETRY"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class SpatialOccupancyRelationship:
    relationship_evidence_id: str
    subject_family: str
    subject_type: str
    subject_id: str
    subject_geometry_reference: str
    relationship_type_code: RelationshipType
    object_family: str
    object_type: str
    object_id: str
    spatial_reference_id: str
    coordinate_candidate_id: str
    evidence_class: str
    evidence_reference: str
    relationship_basis: str
    distance_value: str
    distance_unit: str
    valid_from: str
    valid_to: str
    qualification_status: str
    runtime_effect_scope: str
    notes: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"sprel:nngla:[0-9a-f]{64}", self.relationship_evidence_id) is None:
            raise ValueError("invalid spatial relationship evidence identity")
        if not self.subject_id or not self.object_id:
            raise ValueError("subject_id and object_id are required")
        if self.spatial_reference_id != self.coordinate_candidate_id:
            raise ValueError("Bundle 17C point occupancy uses the coordinate candidate as spatial reference")
        if self.qualification_status != "PASS":
            raise ValueError("persisted occupancy evidence must be factually qualified")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("Bundle 17C source evidence remains SHARED_REFERENCE")


@dataclass(frozen=True, slots=True)
class CompatibilityRule:
    compatibility_rule_code: str
    rule_set_code: str
    subject_family: str
    subject_type_code: str
    relationship_type_code: RelationshipType
    object_family: str
    object_type_code: str
    environment_constraint_code: str
    required_evidence_level: str
    compatibility_outcome: CompatibilityOutcome
    missing_geometry_outcome: CompatibilityOutcome
    context_requirement: str
    priority: int
    symmetric_application: bool
    rationale: str
    status: str
    effective_from: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-COMP-RULE-\d{4}", self.compatibility_rule_code) is None:
            raise ValueError("invalid compatibility rule identity")
        if self.priority < 1:
            raise ValueError("compatibility priority must be positive")
        if self.status != "ACTIVE":
            raise ValueError("Bundle 17C compatibility rules must be active")


@dataclass(frozen=True, slots=True)
class ConflictQualificationResult:
    conflict_result_id: str
    subject_type: str
    subject_id: str
    relationship_type_code: RelationshipType
    object_type: str
    object_id: str
    relationship_evidence_id: str
    conflict_rule_set_code: str
    compatibility_rule_code: str
    geometry_evidence_status: str
    environment_evidence_status: str
    containment_evidence_status: str
    compatibility_outcome: CompatibilityOutcome
    conflict_status: ConflictStatus
    qualification_status: str
    findings: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-CONFLICT-\d{7}", self.conflict_result_id) is None:
            raise ValueError("invalid conflict qualification identity")
        if self.qualification_status not in {"PASS", "PASS_WITH_DEFERRED_GEOMETRY", "FAIL"}:
            raise ValueError("invalid conflict qualification status")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("Bundle 17C evidence remains SHARED_REFERENCE")
        if self.compatibility_outcome is CompatibilityOutcome.BLOCK and self.qualification_status != "FAIL":
            raise ValueError("blocked compatibility must fail qualification")
        if self.conflict_status is ConflictStatus.UNRESOLVED and self.qualification_status != "FAIL":
            raise ValueError("unresolved compatibility must fail closed")


__all__ = [
    "RelationshipType",
    "CompatibilityOutcome",
    "ConflictStatus",
    "SpatialOccupancyRelationship",
    "CompatibilityRule",
    "ConflictQualificationResult",
]
