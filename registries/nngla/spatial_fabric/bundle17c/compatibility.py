"""Data-driven Bundle 17C physical compatibility policy."""
from __future__ import annotations

from functools import lru_cache

from .contracts import CompatibilityOutcome, CompatibilityRule, RelationshipType


def _rule(
    index: int,
    rule_set: str,
    subject_family: str,
    subject_type: str,
    relationship: RelationshipType,
    object_family: str,
    object_type: str,
    outcome: CompatibilityOutcome,
    missing_geometry: CompatibilityOutcome,
    context: str,
    rationale: str,
    *,
    priority: int = 100,
    symmetric: bool = False,
) -> CompatibilityRule:
    return CompatibilityRule(
        compatibility_rule_code=f"NG-COMP-RULE-{index:04d}",
        rule_set_code=rule_set,
        subject_family=subject_family,
        subject_type_code=subject_type,
        relationship_type_code=relationship,
        object_family=object_family,
        object_type_code=object_type,
        environment_constraint_code="",
        required_evidence_level="QUALIFIED_SPATIAL_EVIDENCE",
        compatibility_outcome=outcome,
        missing_geometry_outcome=missing_geometry,
        context_requirement=context,
        priority=priority,
        symmetric_application=symmetric,
        rationale=rationale,
        status="ACTIVE",
        effective_from="2026-08-17",
    )


@lru_cache(maxsize=1)
def compatibility_rules() -> tuple[CompatibilityRule, ...]:
    rules: list[CompatibilityRule] = []
    i = 1
    for feature in ("MOUNTAIN", "VALLEY", "PLATEAU", "PLAIN"):
        rules.append(_rule(i, "NG-CONFLICT-RS-LANDFORM", "NATURAL_FEATURE", feature, RelationshipType.WITHIN,
                           "SOVEREIGN_GROUND", "SOVEREIGN_PART", CompatibilityOutcome.ALLOW,
                           CompatibilityOutcome.REVIEW_REQUIRED, "FULL_FEATURE_EXTENT_REQUIRED_FOR_EXTENT_CONFLICTS",
                           "A qualified natural landform reference point may occupy sovereign land; its full extent remains independently governed."))
        i += 1
    for feature in ("BAY", "BEACH", "CAPE", "CLIFF", "ESTUARY", "NATURAL_HARBOUR"):
        rules.append(_rule(i, "NG-CONFLICT-RS-COASTAL", "NATURAL_FEATURE", feature, RelationshipType.TOUCHES,
                           "SOVEREIGN_GROUND", "SOVEREIGN_BOUNDARY", CompatibilityOutcome.ALLOW_WITH_CONDITION,
                           CompatibilityOutcome.REVIEW_REQUIRED, "PHYSICAL_GEOMETRY_EXTRACTION_REQUIRED_BEFORE_CANONICAL_RECOGNITION",
                           "A source-reserved coastal sector may touch the sovereign coastline, but a reserved sector is not a completed feature geometry."))
        i += 1
    generic = (
        ("NG-CONFLICT-RS-TRANSPORT", "TRANSPORT", "ROAD", RelationshipType.WITHIN, "ADMINISTRATIVE", "ADMINISTRATIVE_AREA", CompatibilityOutcome.ALLOW, CompatibilityOutcome.REVIEW_REQUIRED, "", "Roads may legitimately lie within administrative areas."),
        ("NG-CONFLICT-RS-TRANSPORT", "TRANSPORT", "ROAD", RelationshipType.WITHIN, "SETTLEMENT", "SETTLEMENT", CompatibilityOutcome.ALLOW, CompatibilityOutcome.REVIEW_REQUIRED, "", "Roads may legitimately traverse settlements."),
        ("NG-CONFLICT-RS-TRANSPORT", "TRANSPORT", "ROAD", RelationshipType.CROSSES, "HYDROLOGY", "RIVER", CompatibilityOutcome.ALLOW_WITH_CONDITION, CompatibilityOutcome.REVIEW_REQUIRED, "CROSSING_INFRASTRUCTURE_OR_ENGINEERING_APPROVAL_REQUIRED", "A road-river crossing is spatially valid but requires a governed crossing solution."),
        ("NG-CONFLICT-RS-SETTLEMENT", "SETTLEMENT", "SETTLEMENT", RelationshipType.WITHIN, "MARINE", "MARINE_WATERBODY", CompatibilityOutcome.BLOCK, CompatibilityOutcome.BLOCK, "", "An ordinary land settlement cannot be accepted as lying within open marine water solely as a land settlement."),
        ("NG-CONFLICT-RS-CADASTRE", "CADASTRE", "PARCEL", RelationshipType.OVERLAPS, "CADASTRE", "PARCEL", CompatibilityOutcome.ALLOW_WITH_CONDITION, CompatibilityOutcome.REVIEW_REQUIRED, "CADASTRAL_LINEAGE_OPERATION_REQUIRED", "Parcel overlap is rejected unless a governed subdivision/consolidation/lineage operation explicitly supplies the context."),
        ("NG-CONFLICT-RS-COASTAL", "COASTAL", "COASTLINE", RelationshipType.TOUCHES, "MARINE", "MARINE_WATERBODY", CompatibilityOutcome.ALLOW, CompatibilityOutcome.REVIEW_REQUIRED, "", "A coastline is the governed interface between land and a marine waterbody."),
    )
    for row in generic:
        rules.append(_rule(i, *row))
        i += 1
    return tuple(rules)


def compatibility_rule_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "compatibility_rule_code": r.compatibility_rule_code,
        "rule_set_code": r.rule_set_code,
        "subject_family": r.subject_family,
        "subject_type_code": r.subject_type_code,
        "relationship_type_code": r.relationship_type_code.value,
        "object_family": r.object_family,
        "object_type_code": r.object_type_code,
        "environment_constraint_code": r.environment_constraint_code,
        "required_evidence_level": r.required_evidence_level,
        "compatibility_outcome": r.compatibility_outcome.value,
        "missing_geometry_outcome": r.missing_geometry_outcome.value,
        "context_requirement": r.context_requirement,
        "priority": str(r.priority),
        "symmetric_application": str(r.symmetric_application).lower(),
        "rationale": r.rationale,
        "status": r.status,
        "effective_from": r.effective_from,
    } for r in compatibility_rules())


def find_rule(subject_family: str, subject_type: str, relationship: str, object_family: str, object_type: str) -> CompatibilityRule | None:
    matches = [r for r in compatibility_rules() if (
        r.subject_family == subject_family
        and r.subject_type_code == subject_type
        and r.relationship_type_code.value == relationship
        and r.object_family == object_family
        and r.object_type_code == object_type
    )]
    return min(matches, key=lambda r: r.priority) if matches else None


def evaluate_compatibility(
    subject_family: str,
    subject_type: str,
    relationship: str,
    object_family: str,
    object_type: str,
    *,
    geometry_complete: bool,
    supplied_contexts: tuple[str, ...] = (),
) -> CompatibilityOutcome:
    """Evaluate a known relation fail-closed without inventing missing evidence."""
    rule = find_rule(subject_family, subject_type, relationship, object_family, object_type)
    if rule is None:
        return CompatibilityOutcome.NOT_EVALUABLE
    if not geometry_complete:
        return rule.missing_geometry_outcome
    if rule.context_requirement and rule.context_requirement not in set(supplied_contexts):
        return CompatibilityOutcome.BLOCK
    return rule.compatibility_outcome


__all__ = ["compatibility_rules", "compatibility_rule_rows", "find_rule", "evaluate_compatibility"]
