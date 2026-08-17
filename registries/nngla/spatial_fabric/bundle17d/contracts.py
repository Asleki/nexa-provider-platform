"""P006.7.11.7 Bundle 17D marine namespace and qualification contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class MarineSubjectType(str, Enum):
    MARINE_WATERBODY = "MARINE_WATERBODY"
    COASTAL_INTERFACE = "COASTAL_INTERFACE"
    MARINE_ANCHOR = "MARINE_ANCHOR"
    SEA_ROUTE = "SEA_ROUTE"
    MARINE_CONNECTION = "MARINE_CONNECTION"
    ISLAND_PHYSICAL_STATE = "ISLAND_PHYSICAL_STATE"


@dataclass(frozen=True, slots=True)
class FeatureTypeExtension:
    feature_type_code: str
    feature_family_code: str
    canonical_label: str
    geometry_expectation: str
    origin_class: str
    nngla_recognizable: bool
    nngla_creatable: bool
    nameable: bool
    supports_history: bool
    status: str
    effective_from: str
    effective_to: str
    description: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]+", self.feature_type_code):
            raise ValueError("invalid feature type extension code")
        if self.origin_class != "NATURAL":
            raise ValueError("Bundle 17D feature extensions are natural physical geography")
        if self.nngla_creatable:
            raise ValueError("NNGLA recognizes natural geography; it does not physically create it")
        if not self.nngla_recognizable or self.status != "ACTIVE":
            raise ValueError("Bundle 17D extensions must be active recognizable types")


@dataclass(frozen=True, slots=True)
class MarineRouteType:
    marine_route_type_code: str
    canonical_label: str
    connection_type: str
    geometry_type_code: str
    start_anchor_role: str
    end_anchor_role: str
    interior_spatial_requirement: str
    endpoint_spatial_requirement: str
    may_cross_land: bool
    physical_qualification_requires_name: bool
    supports_history: bool
    status: str
    effective_from: str
    description: str

    def __post_init__(self) -> None:
        if self.geometry_type_code != "LINESTRING":
            raise ValueError("current New Waters route type is LINESTRING")
        if self.may_cross_land:
            raise ValueError("current anonymous New Waters routes may not cross land")
        if self.physical_qualification_requires_name:
            raise ValueError("physical route qualification is independent of naming")
        if self.status != "ACTIVE":
            raise ValueError("marine route types must be active")


@dataclass(frozen=True, slots=True)
class MarineSpatialQualificationResult:
    marine_qualification_id: str
    subject_type: MarineSubjectType
    subject_id: str
    marine_waterbody_id: str
    governed_feature_type_code: str
    marine_route_type_code: str
    source_geometry_status: str
    coordinate_qualification_status: str
    containment_context: str
    land_overlap_status: str
    source_fidelity_status: str
    derivation_lineage_status: str
    naming_status: str
    sovereignty_assertion_status: str
    publication_status: str
    qualification_status: str
    findings: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-MAR-QUAL-\d{6}", self.marine_qualification_id) is None:
            raise ValueError("invalid marine qualification identity")
        if not self.subject_id or not self.marine_waterbody_id:
            raise ValueError("marine subject and waterbody identity are required")
        if self.qualification_status not in {"PASS", "PASS_WITH_KNOWN_GEOMETRY_LIMITATION", "FAIL"}:
            raise ValueError("invalid marine qualification status")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("Bundle 17D source evidence remains SHARED_REFERENCE")


__all__ = ["MarineSubjectType", "FeatureTypeExtension", "MarineRouteType", "MarineSpatialQualificationResult"]
