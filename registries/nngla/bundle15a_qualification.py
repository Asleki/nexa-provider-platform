"""P006.7.3/P006.7.4 end-to-end Bundle 15A qualification."""
from __future__ import annotations
from dataclasses import dataclass
from .bundle15a_source import load_feature_types, load_naming_statuses, load_gazette_actions, load_feature_recognitions, load_settlement_names, load_places, load_administrative_areas, load_feature_name_assignments
from .place_hierarchy import qualify_place_hierarchy
from .schema15a_contract import load_schema15a_sql, qualify_schema15a_sql

QUALIFICATION_ID = "qualification:novegeo:nngla-bundle15a:v1"

@dataclass(frozen=True, slots=True)
class Bundle15AQualificationReceipt:
    qualification_id: str
    status: str
    findings: tuple[str, ...]
    feature_type_count: int
    recognized_feature_candidate_count: int
    settlement_place_count: int
    administrative_candidate_count: int
    feature_name_assignment_count: int


def qualify_bundle15a() -> Bundle15AQualificationReceipt:
    feature_types = load_feature_types()
    naming = load_naming_statuses()
    gazette = load_gazette_actions()
    features = load_feature_recognitions()
    names = load_settlement_names()
    places = load_places()
    areas = load_administrative_areas()
    assignments = load_feature_name_assignments()
    findings: list[str] = []
    if len(places) != 700: findings.append(f"settlement-place-count:{len(places)}")
    if len(areas) != 192: findings.append(f"administrative-candidate-count:{len(areas)}")
    if len(features) != 21: findings.append(f"feature-candidate-count:{len(features)}")
    if len(assignments) != 20: findings.append(f"feature-name-assignment-count:{len(assignments)}")
    if len(names) != len(places): findings.append("settlement-name-place-cardinality-mismatch")
    if any(p.has_authoritative_geometry for p in places): findings.append("place-source-must-remain-unmapped-at-bundle15a")
    if any(a.geometry_reference for a in areas): findings.append("administrative-boundary-geometry-must-remain-deferred")
    if any(a.assignment_status != "PROPOSED_UNGAZETTED" for a in assignments): findings.append("feature-name-assignments-must-remain-proposed-ungazetted")
    if not any(x.naming_status_code == "ACTIVE_OFFICIAL" and x.can_display_publicly for x in naming): findings.append("missing-public-official-naming-state")
    if not any(x.gazette_action_code == "NAME" and x.creates_legal_effect for x in gazette): findings.append("missing-name-gazette-action")
    if any(x.origin_class.value == "NATURAL" and x.nngla_creatable for x in feature_types): findings.append("natural-feature-creation-policy-violation")
    findings.extend(qualify_place_hierarchy(places, areas))
    findings.extend(qualify_schema15a_sql(load_schema15a_sql()))
    return Bundle15AQualificationReceipt(QUALIFICATION_ID, "QUALIFIED" if not findings else "FAILED", tuple(findings), len(feature_types), len(features), len(places), len(areas), len(assignments))

__all__ = ["QUALIFICATION_ID", "Bundle15AQualificationReceipt", "qualify_bundle15a"]
