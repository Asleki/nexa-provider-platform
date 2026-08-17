"""Bundle 17C fail-closed conflict qualification."""
from __future__ import annotations

from functools import lru_cache

from .compatibility import find_rule
from .contracts import CompatibilityOutcome, ConflictQualificationResult, ConflictStatus
from .occupancy import candidate_row_by_id, derive_occupancy_relationships


def _geometry_status(source_row: dict[str, str]) -> str:
    raw = source_row.get("geometry_status", "")
    if raw == "QUALIFIED_REFERENCE_POINT_EXTENT_NOT_YET_AUTHORED":
        return "REFERENCE_POINT_ONLY_EXTENT_PENDING"
    if raw == "SOURCE_RESERVED_SECTOR_PENDING_PHYSICAL_GEOMETRY_EXTRACTION":
        return "BOUNDARY_SECTOR_ONLY_EXTRACTION_PENDING"
    return "UNKNOWN_GEOMETRY_EVIDENCE"


@lru_cache(maxsize=1)
def derive_conflict_qualification_results() -> tuple[ConflictQualificationResult, ...]:
    source_by_id = candidate_row_by_id()
    out: list[ConflictQualificationResult] = []
    for index, relationship in enumerate(derive_occupancy_relationships(), start=1):
        source_row = source_by_id[relationship.subject_id]
        rule = find_rule(
            relationship.subject_family,
            relationship.subject_type,
            relationship.relationship_type_code.value,
            relationship.object_family,
            relationship.object_type,
        )
        geometry_status = _geometry_status(source_row)
        if rule is None:
            outcome = CompatibilityOutcome.NOT_EVALUABLE
            conflict = ConflictStatus.UNRESOLVED
            qualification = "FAIL"
            rule_set = ""
            rule_code = ""
            findings = "NO_MATCHING_COMPATIBILITY_RULE_FAIL_CLOSED"
        elif geometry_status == "UNKNOWN_GEOMETRY_EVIDENCE":
            outcome = rule.missing_geometry_outcome
            conflict = ConflictStatus.UNRESOLVED
            qualification = "FAIL"
            rule_set = rule.rule_set_code
            rule_code = rule.compatibility_rule_code
            findings = "UNKNOWN_GEOMETRY_EVIDENCE_FAIL_CLOSED"
        else:
            outcome = rule.compatibility_outcome
            rule_set = rule.rule_set_code
            rule_code = rule.compatibility_rule_code
            if outcome is CompatibilityOutcome.BLOCK:
                conflict = ConflictStatus.CONFLICT
                qualification = "FAIL"
                findings = "COMPATIBILITY_POLICY_BLOCKED_RELATION"
            else:
                conflict = ConflictStatus.NOT_EVALUABLE_PENDING_GEOMETRY
                qualification = "PASS_WITH_DEFERRED_GEOMETRY"
                findings = "LOCATION_RELATION_QUALIFIED;FULL_EXTENT_CONFLICT_CHECK_DEFERRED_UNTIL_AUTHORITATIVE_GEOMETRY"
        out.append(ConflictQualificationResult(
            conflict_result_id=f"NG-CONFLICT-{index:07d}",
            subject_type=relationship.subject_type,
            subject_id=relationship.subject_id,
            relationship_type_code=relationship.relationship_type_code,
            object_type=relationship.object_type,
            object_id=relationship.object_id,
            relationship_evidence_id=relationship.relationship_evidence_id,
            conflict_rule_set_code=rule_set,
            compatibility_rule_code=rule_code,
            geometry_evidence_status=geometry_status,
            environment_evidence_status="NOT_REQUIRED_FOR_REFERENCE_RELATION_QUALIFICATION",
            containment_evidence_status="PASS",
            compatibility_outcome=outcome,
            conflict_status=conflict,
            qualification_status=qualification,
            findings=findings,
            runtime_effect_scope="SHARED_REFERENCE",
        ))
    return tuple(out)


def conflict_findings(rows: tuple[ConflictQualificationResult, ...] | None = None) -> tuple[str, ...]:
    current = rows or derive_conflict_qualification_results()
    return tuple(f"{row.subject_id}:{row.findings}" for row in current if row.qualification_status == "FAIL")


def bundle17c_is_qualified() -> bool:
    rows = derive_conflict_qualification_results()
    return bool(rows) and not conflict_findings(rows) and all(
        row.qualification_status in {"PASS", "PASS_WITH_DEFERRED_GEOMETRY"} for row in rows
    )


__all__ = ["derive_conflict_qualification_results", "conflict_findings", "bundle17c_is_qualified"]
