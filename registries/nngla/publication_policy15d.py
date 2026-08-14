"""P006.7.9 public read-model visibility policy.

This module is additive to the locked Bundle 14C publication infrastructure.
It does not publish canonical records.  It determines whether derived NNGLA
read-model subjects are eligible to appear in the public PWA/API surface.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from .bundle15a_source import load_naming_statuses


class PublicReadVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True, slots=True)
class PublicReadDecision:
    visibility: PublicReadVisibility
    map_renderable: bool
    reasons: tuple[str, ...]

    @property
    def public_eligible(self) -> bool:
        return self.visibility is PublicReadVisibility.PUBLIC and not self.reasons


def _public_name_states() -> frozenset[str]:
    return frozenset(
        item.naming_status_code
        for item in load_naming_statuses()
        if item.can_display_publicly
    )


PUBLIC_NAME_STATES = _public_name_states()


def decide_place_visibility(*, naming_status_code: str, spatial_assignment_status: str, published_through_gate: bool = False) -> PublicReadDecision:
    reasons: list[str] = []
    if naming_status_code not in PUBLIC_NAME_STATES:
        reasons.append("NAME_NOT_PUBLIC")
    mapped = spatial_assignment_status not in {"UNMAPPED_PENDING_ASSOCIATION", "UNMAPPED"}
    if not published_through_gate:
        reasons.append("NO_NNGLA_PUBLICATION_RECORD")
    if not mapped:
        reasons.append("NO_AUTHORITATIVE_SPATIAL_ASSIGNMENT")
    visibility = PublicReadVisibility.PUBLIC if not reasons else PublicReadVisibility.INTERNAL
    return PublicReadDecision(visibility, visibility is PublicReadVisibility.PUBLIC and mapped, tuple(reasons))


def decide_administrative_area_visibility(*, lifecycle_status: str, boundary_status: str, geometry_reference: str | None, published_through_gate: bool = False) -> PublicReadDecision:
    reasons: list[str] = []
    if lifecycle_status not in {"ACTIVE", "GAZETTED"}:
        reasons.append("ADMIN_AREA_NOT_LEGALLY_ACTIVE")
    if boundary_status not in {"LEGALIZED", "GAZETTED", "ACTIVE"}:
        reasons.append("BOUNDARY_NOT_LEGALIZED")
    if not geometry_reference:
        reasons.append("NO_AUTHORITATIVE_GEOMETRY")
    if not published_through_gate:
        reasons.append("NO_NNGLA_PUBLICATION_RECORD")
    visibility = PublicReadVisibility.PUBLIC if not reasons else PublicReadVisibility.INTERNAL
    return PublicReadDecision(visibility, visibility is PublicReadVisibility.PUBLIC, tuple(reasons))


def decide_feature_visibility(*, naming_status_code: str | None, publication_status: str | None, published_through_gate: bool = False) -> PublicReadDecision:
    reasons: list[str] = []
    if naming_status_code not in PUBLIC_NAME_STATES:
        reasons.append("FEATURE_NAME_NOT_PUBLIC")
    if publication_status != "PUBLISHED":
        reasons.append("FEATURE_GEOMETRY_NOT_PUBLISHED")
    if not published_through_gate:
        reasons.append("NO_NNGLA_PUBLICATION_RECORD")
    visibility = PublicReadVisibility.PUBLIC if not reasons else PublicReadVisibility.INTERNAL
    return PublicReadDecision(visibility, visibility is PublicReadVisibility.PUBLIC, tuple(reasons))


def decide_road_visibility(*, planning_status: str, geometry_status: str, geometry_reference: str | None, published_through_gate: bool = False) -> PublicReadDecision:
    reasons: list[str] = []
    if planning_status in {"RESERVED_REFERENCE", "PROPOSED", "PLANNED"}:
        reasons.append("ROAD_NOT_OPERATIONALLY_ACTIVE")
    if geometry_status in {"UNMAPPED_PENDING_CONSTRUCTION_OR_SURVEY", "UNMAPPED"} or not geometry_reference:
        reasons.append("ROAD_NOT_AUTHORITATIVELY_MAPPED")
    if not published_through_gate:
        reasons.append("NO_NNGLA_PUBLICATION_RECORD")
    visibility = PublicReadVisibility.PUBLIC if not reasons else PublicReadVisibility.INTERNAL
    return PublicReadDecision(visibility, visibility is PublicReadVisibility.PUBLIC, tuple(reasons))


def decide_address_visibility(*, lifecycle_status: str, has_site: bool, published_through_gate: bool = False) -> PublicReadDecision:
    reasons: list[str] = []
    if lifecycle_status not in {"ACTIVE", "ASSIGNED"}:
        reasons.append("ADDRESS_NOT_ACTIVE")
    if not has_site:
        reasons.append("ADDRESS_SITE_REQUIRED")
    if not published_through_gate:
        reasons.append("NO_NNGLA_PUBLICATION_RECORD")
    visibility = PublicReadVisibility.PUBLIC if not reasons else PublicReadVisibility.INTERNAL
    return PublicReadDecision(visibility, visibility is PublicReadVisibility.PUBLIC, tuple(reasons))


def decide_parcel_visibility(*, parcel_status: str, geometry_reference: str | None, published_through_gate: bool = False) -> PublicReadDecision:
    reasons: list[str] = []
    if parcel_status not in {"REGISTERED", "ACTIVE"}:
        reasons.append("PARCEL_NOT_PUBLICLY_REGISTERED")
    if not geometry_reference:
        reasons.append("PARCEL_GEOMETRY_REQUIRED")
    if not published_through_gate:
        reasons.append("NO_NNGLA_PUBLICATION_RECORD")
    visibility = PublicReadVisibility.PUBLIC if not reasons else PublicReadVisibility.RESTRICTED
    return PublicReadDecision(visibility, visibility is PublicReadVisibility.PUBLIC, tuple(reasons))


def title_public_visibility() -> PublicReadDecision:
    return PublicReadDecision(PublicReadVisibility.RESTRICTED, False, ("TITLE_DISCLOSURE_POLICY_DEFERRED",))


__all__ = [
    "PublicReadVisibility", "PublicReadDecision", "PUBLIC_NAME_STATES",
    "decide_place_visibility", "decide_administrative_area_visibility",
    "decide_feature_visibility", "decide_road_visibility", "decide_address_visibility",
    "decide_parcel_visibility", "title_public_visibility",
]
