"""Stable contracts for P006.7.11.10 place spatial association."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from ._shared import CRS_CODE, EFFECT_SCOPE

_PLACE_ID = re.compile(r"^NG-PLC-\d{6}$")
_SOURCE_PLACE_ID = re.compile(r"^NGP-\d{6}$")
_SPATIAL_POINT_ID = re.compile(r"^NG-SPT-\d{6}$")
_GEOMETRY_ID = re.compile(r"^NG-GEO-\d{6}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class GeometryRole(str, Enum):
    PLACE_REFERENCE_POINT = "PLACE_REFERENCE_POINT"
    SETTLEMENT_FOOTPRINT = "SETTLEMENT_FOOTPRINT"


class SpatialOutcomeStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    QUALIFIED_WITH_EXCEPTION = "QUALIFIED_WITH_EXCEPTION"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class SettlementSitingRequirement:
    source_place_code: str
    place_id: str
    settlement_name_record_id: str
    canonical_name: str
    place_type_code: str
    settlement_scale: str
    urbanity: str
    parent_source_place_code: str
    major_city_source_place_code: str
    region_code: str
    region_name: str
    terrain_zone_code: str
    location_character: str
    dominant_function: str
    source_dataset_id: str
    source_sha256: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if _SOURCE_PLACE_ID.fullmatch(self.source_place_code) is None:
            raise ValueError("invalid source place identity")
        if _PLACE_ID.fullmatch(self.place_id) is None:
            raise ValueError("invalid canonical place identity")
        if not self.settlement_name_record_id.startswith("NG-NAM-SET-"):
            raise ValueError("invalid settlement name identity")
        if not self.canonical_name.strip() or not self.place_type_code.strip() or not self.region_code.strip():
            raise ValueError("place name, type and region are required")
        if self.runtime_effect_scope != EFFECT_SCOPE:
            raise ValueError("place geography must remain SHARED_REFERENCE")
        if _SHA256.fullmatch(self.source_sha256) is None:
            raise ValueError("place source digest must be SHA-256")


@dataclass(frozen=True, slots=True)
class SpatialSupportPoint:
    spatial_point_id: str
    longitude: float
    latitude: float
    sovereign_part_id: str
    sovereign_land_relation: str
    terrain_class: str = ""
    elevation_m: float | None = None
    annual_rainfall_mm: float | None = None
    climate_class: str = ""
    vegetation_class: str = ""
    aridity_class: str = ""
    hydrology_reference_id: str = ""

    def __post_init__(self) -> None:
        if _SPATIAL_POINT_ID.fullmatch(self.spatial_point_id) is None:
            raise ValueError("invalid canonical spatial support identity")
        if not -180 <= self.longitude <= 180 or not -90 <= self.latitude <= 90:
            raise ValueError("invalid support coordinate")
        if self.sovereign_land_relation != "INSIDE_SOVEREIGN_LAND":
            raise ValueError("place support points must use qualified interior sovereign references")


@dataclass(frozen=True, slots=True)
class PlaceReferencePointCandidate:
    reference_candidate_id: str
    source_place_code: str
    place_id: str
    canonical_name: str
    place_type_code: str
    region_code: str
    parent_source_place_code: str
    longitude: float
    latitude: float
    crs_code: str
    sovereign_part_id: str
    supporting_spatial_point_id: str
    support_distance_m: float
    placement_basis: str
    geometry_reservation_key: str
    outcome_status: SpatialOutcomeStatus
    exception_code: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if not self.reference_candidate_id.startswith("placeref:nngla:"):
            raise ValueError("invalid place-reference candidate identity")
        if _SOURCE_PLACE_ID.fullmatch(self.source_place_code) is None or _PLACE_ID.fullmatch(self.place_id) is None:
            raise ValueError("invalid place identity")
        if _SPATIAL_POINT_ID.fullmatch(self.supporting_spatial_point_id) is None:
            raise ValueError("invalid supporting spatial point")
        if not -180 <= self.longitude <= 180 or not -90 <= self.latitude <= 90:
            raise ValueError("invalid place reference coordinate")
        if self.crs_code != CRS_CODE:
            raise ValueError("place reference coordinate must use governed WGS84 CRS")
        if self.support_distance_m < 0:
            raise ValueError("support distance cannot be negative")
        if not self.geometry_reservation_key.startswith("p006.7.11.10:place-reference:"):
            raise ValueError("invalid geometry reservation key")
        if self.runtime_effect_scope != EFFECT_SCOPE:
            raise ValueError("place reference must remain SHARED_REFERENCE")
        if self.outcome_status is SpatialOutcomeStatus.FAILED:
            raise ValueError("failed place reference candidates cannot enter qualified bundle")
        if self.outcome_status is SpatialOutcomeStatus.QUALIFIED_WITH_EXCEPTION and not self.exception_code:
            raise ValueError("qualified exception requires an exception code")
        if self.outcome_status is SpatialOutcomeStatus.QUALIFIED and self.exception_code:
            raise ValueError("ordinary qualified outcome cannot carry exception code")


@dataclass(frozen=True, slots=True)
class SettlementFootprintCandidate:
    footprint_candidate_id: str
    source_place_code: str
    place_id: str
    canonical_name: str
    place_type_code: str
    region_code: str
    geometry_role_code: GeometryRole
    geometry_type_code: str
    ring: tuple[tuple[float, float], ...]
    nominal_radius_km: float
    realized_radius_km: float
    area_sq_km: float
    crs_code: str
    sovereign_part_id: str
    geometry_reservation_key: str
    qualification_status: str
    source_basis: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if not self.footprint_candidate_id.startswith("placefootprint:nngla:"):
            raise ValueError("invalid settlement-footprint candidate identity")
        if _PLACE_ID.fullmatch(self.place_id) is None or _SOURCE_PLACE_ID.fullmatch(self.source_place_code) is None:
            raise ValueError("invalid footprint subject identity")
        if self.geometry_role_code is not GeometryRole.SETTLEMENT_FOOTPRINT or self.geometry_type_code != "POLYGON":
            raise ValueError("settlement footprint must be an independent POLYGON role")
        if self.crs_code != CRS_CODE or self.runtime_effect_scope != EFFECT_SCOPE:
            raise ValueError("invalid footprint CRS/effect scope")
        if len(self.ring) < 4 or self.ring[0] != self.ring[-1]:
            raise ValueError("footprint ring must be closed and contain at least four coordinates")
        if self.nominal_radius_km <= 0 or self.realized_radius_km <= 0 or self.area_sq_km <= 0:
            raise ValueError("footprint dimensions must be positive")
        if self.realized_radius_km > self.nominal_radius_km + 1e-9:
            raise ValueError("realized footprint radius cannot exceed policy radius")
        if not self.geometry_reservation_key.startswith("p006.7.11.10:settlement-footprint:"):
            raise ValueError("invalid footprint geometry reservation key")
        if self.qualification_status != "QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY":
            raise ValueError("settlement footprint must remain explicitly non-legal")


@dataclass(frozen=True, slots=True)
class PointOnlyException:
    source_place_code: str
    place_id: str
    reason_code: str
    reason_detail: str

    def __post_init__(self) -> None:
        if _PLACE_ID.fullmatch(self.place_id) is None or not self.reason_code:
            raise ValueError("point-only exception requires canonical place and reason")


@dataclass(frozen=True, slots=True)
class PlaceSpatialRelationshipEvidence:
    relationship_evidence_id: str
    child_place_id: str
    child_source_place_code: str
    parent_place_id: str
    parent_source_place_code: str
    distance_m: float
    parent_footprint_relation: str
    relationship_basis: str
    qualification_status: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if not self.relationship_evidence_id.startswith("placerel:nngla:"):
            raise ValueError("invalid place relationship evidence identity")
        if _PLACE_ID.fullmatch(self.child_place_id) is None or _PLACE_ID.fullmatch(self.parent_place_id) is None:
            raise ValueError("invalid parent/child place identity")
        if self.child_place_id == self.parent_place_id or self.distance_m < 0:
            raise ValueError("invalid parent/child spatial relationship")
        if self.parent_footprint_relation not in {"WITHIN", "OUTSIDE", "PARENT_HAS_NO_FOOTPRINT"}:
            raise ValueError("invalid parent footprint relation")
        if self.qualification_status != "PASS" or self.runtime_effect_scope != EFFECT_SCOPE:
            raise ValueError("parent/child spatial evidence must be qualified shared reference")


@dataclass(frozen=True, slots=True)
class GeometryReservation:
    reservation_id: str
    idempotency_key: str
    subject_id: str
    geometry_role_code: GeometryRole

    def __post_init__(self) -> None:
        if not self.reservation_id.startswith("georeserve:place:nngla:"):
            raise ValueError("invalid place geometry reservation identity")
        if _PLACE_ID.fullmatch(self.subject_id) is None or not self.idempotency_key:
            raise ValueError("invalid geometry reservation subject/key")


@dataclass(frozen=True, slots=True)
class PersistedGeometryReference:
    geometry_id: str
    subject_id: str
    geometry_role_code: GeometryRole

    def __post_init__(self) -> None:
        if _GEOMETRY_ID.fullmatch(self.geometry_id) is None or _PLACE_ID.fullmatch(self.subject_id) is None:
            raise ValueError("invalid persisted geometry reference")


@dataclass(frozen=True, slots=True)
class PlaceSpatialExecutionReceipt:
    execution_id: str
    fingerprint_sha256: str
    database_name: str
    environment_name: str
    repository_revision: str
    submitter_actor_id: str
    approver_actor_id: str
    selected_place_count: int
    associated_place_count: int
    geometry_insert_count: int
    footprint_insert_count: int
    point_only_count: int
    status: str
    replayed: bool

    def __post_init__(self) -> None:
        if not self.execution_id.startswith("nnglarun:place-spatial:"):
            raise ValueError("invalid place-spatial execution identity")
        if _SHA256.fullmatch(self.fingerprint_sha256) is None:
            raise ValueError("execution fingerprint must be SHA-256")
        if self.submitter_actor_id == self.approver_actor_id:
            raise ValueError("submitter and approver must remain separate")
        if not self.database_name.strip() or not self.environment_name.strip() or not self.repository_revision.strip():
            raise ValueError("execution target and repository revision are required")
        if not self.submitter_actor_id.strip() or not self.approver_actor_id.strip():
            raise ValueError("submitter and approver actors are required")
        if self.selected_place_count != 700 or self.selected_place_count != self.associated_place_count:
            raise ValueError("Bundle 19A must associate exactly all 700 canonical places")
        if self.footprint_insert_count + self.point_only_count != self.selected_place_count:
            raise ValueError("every place must have either a footprint or an explicit point-only outcome")
        if self.geometry_insert_count != self.selected_place_count + self.footprint_insert_count:
            raise ValueError("geometry count must equal 700 reference points plus settlement footprints")
        if self.status not in {"APPLIED", "REUSED"}:
            raise ValueError("invalid place-spatial execution status")
        if self.replayed != (self.status == "REUSED"):
            raise ValueError("replay flag/status mismatch")


__all__ = [
    "GeometryRole", "SpatialOutcomeStatus", "SettlementSitingRequirement", "SpatialSupportPoint",
    "PlaceReferencePointCandidate", "SettlementFootprintCandidate", "PointOnlyException",
    "PlaceSpatialRelationshipEvidence", "GeometryReservation", "PersistedGeometryReference",
    "PlaceSpatialExecutionReceipt",
]
