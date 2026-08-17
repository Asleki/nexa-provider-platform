"""Bundle 17H smart-addressing and addressable-site contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import re

_ADDRESS_RE = re.compile(r"^NG-ADR-\d{6}$")
_ROAD_RE = re.compile(r"^NG-RD-\d{6}$")
_PARCEL_RE = re.compile(r"^NV-\d{2}-\d{3}-\d{4,}$")
_GEO_RE = re.compile(r"^NG-GEO-\d{6}$")
_PLACE_RE = re.compile(r"^NG-PLC-\d{6}$")
_ADMIN_RE = re.compile(r"^NG-ADM-\d{6}$")


class AddressAllocationPolicy(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    LOCAL_RESET = "LOCAL_RESET"
    SEGMENT_RESET = "SEGMENT_RESET"
    ODD_EVEN = "ODD_EVEN"
    SEQUENTIAL = "SEQUENTIAL"
    CUSTOM_GOVERNED = "CUSTOM_GOVERNED"


class SiteLifecycleStage(str, Enum):
    CANDIDATE = "CANDIDATE"
    SPATIALLY_QUALIFIED = "SPATIALLY_QUALIFIED"
    ADDRESS_ELIGIBLE = "ADDRESS_ELIGIBLE"
    ADDRESS_ASSIGNED = "ADDRESS_ASSIGNED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class RoadSegmentCandidate:
    road_segment_id: str
    road_id: str
    source_road_candidate_id: str
    segment_sequence: int
    segment_role: str
    geometry_id: str
    start_measure_m: str
    end_measure_m: str
    geometry_status: str
    addressing_scope_eligible: bool
    runtime_effect_scope: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.road_segment_id.startswith("roadseg:nngla:"):
            raise ValueError("road segment must use private subordinate roadseg:nngla identity")
        if _ROAD_RE.fullmatch(self.road_id) is None:
            raise ValueError("road segment must reference canonical NG-RD identity")
        if not re.fullmatch(r"NG-RD-CAND-\d{6}", self.source_road_candidate_id):
            raise ValueError("road segment source candidate identity invalid")
        if self.segment_sequence < 1:
            raise ValueError("segment sequence must be positive")
        if self.geometry_id and _GEO_RE.fullmatch(self.geometry_id) is None:
            raise ValueError("segment geometry must use governed geometry identity")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("baseline road segmentation remains shared reference")


@dataclass(frozen=True, slots=True)
class RoadFrontageCandidate:
    frontage_id: str
    site_id: str
    road_id: str
    road_segment_id: str
    frontage_role: str
    access_status: str
    qualification_status: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.frontage_id.startswith("frontage:nngla:"):
            raise ValueError("frontage identity invalid")
        if not self.site_id.startswith("site:nngla:"):
            raise ValueError("frontage site identity invalid")
        if _ROAD_RE.fullmatch(self.road_id) is None:
            raise ValueError("frontage road identity invalid")
        if not self.road_segment_id.startswith("roadseg:nngla:"):
            raise ValueError("frontage segment identity invalid")
        if self.frontage_role not in {"PRIMARY", "SECONDARY", "SERVICE", "PEDESTRIAN", "EMERGENCY"}:
            raise ValueError("unsupported frontage role")


@dataclass(frozen=True, slots=True)
class AddressAllocationPolicyDefinition:
    policy_code: AddressAllocationPolicy
    allocation_scope: str
    reset_semantics: str
    default_sequence_step: int
    duplicate_visible_number_cross_scope_allowed: bool
    same_scope_collision_policy: str
    status: str

    def __post_init__(self) -> None:
        if self.default_sequence_step < 1:
            raise ValueError("address sequence step must be positive")
        if self.same_scope_collision_policy != "FAIL_CLOSED":
            raise ValueError("same-scope collisions must fail closed")
        if self.status != "ACTIVE":
            raise ValueError("address allocation policy must be active")


@dataclass(frozen=True, slots=True)
class AddressSeriesDefinition:
    series_id: str
    road_id: str
    road_segment_id: str
    policy_code: AddressAllocationPolicy | str
    scope_type: str
    scope_reference: str
    start_number: int
    sequence_step: int
    number_format_rule_code: str
    side_rule: str
    allow_suffix: bool
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if not self.series_id.startswith("addrseries:nngla:"):
            raise ValueError("address series identity invalid")
        if _ROAD_RE.fullmatch(self.road_id) is None:
            raise ValueError("address series road identity invalid")
        if self.road_segment_id and not self.road_segment_id.startswith("roadseg:nngla:"):
            raise ValueError("address series road segment identity invalid")
        policy = self.policy_code if isinstance(self.policy_code, AddressAllocationPolicy) else AddressAllocationPolicy(str(self.policy_code))
        object.__setattr__(self, "policy_code", policy)
        if self.scope_type not in {"ROAD", "ROAD_SEGMENT", "LOCAL_GOVERNED_SCOPE", "CUSTOM_GOVERNED_SCOPE"}:
            raise ValueError("unsupported address series scope type")
        if self.start_number < 0 or self.sequence_step < 1:
            raise ValueError("invalid address series sequence configuration")
        if policy is AddressAllocationPolicy.ODD_EVEN and self.sequence_step != 2:
            raise ValueError("ODD_EVEN series requires sequence_step=2")
        if self.side_rule not in {"NONE", "ODD", "EVEN", "GOVERNED"}:
            raise ValueError("unsupported address side rule")
        if self.status != "ACTIVE":
            raise ValueError("address series must be active")


@dataclass(frozen=True, slots=True)
class AddressNumberReservation:
    reservation_id: str
    series_id: str
    site_id: str
    reserved_address_id: str
    display_address_number: str
    normalized_number_key: str
    idempotency_key: str
    reservation_status: str
    canonical_address_created: bool
    authority_runtime_mode: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.reservation_id.startswith("addrres:nngla:"):
            raise ValueError("address reservation identity invalid")
        if not self.series_id.startswith("addrseries:nngla:"):
            raise ValueError("address reservation series invalid")
        if not self.site_id.startswith("site:nngla:"):
            raise ValueError("address reservation site invalid")
        if _ADDRESS_RE.fullmatch(self.reserved_address_id) is None:
            raise ValueError("reserved address identity must use governed NG-ADR namespace")
        if not self.display_address_number or not self.normalized_number_key:
            raise ValueError("display and normalized number required")
        if not self.idempotency_key:
            raise ValueError("address reservation requires idempotency key")
        if self.reservation_status != "RESERVED" or self.canonical_address_created:
            raise ValueError("address number reservation must remain pre-canonical")
        if self.authority_runtime_mode != "production":
            raise ValueError("sovereign address number reservation is production-authority operation")


@dataclass(frozen=True, slots=True)
class HouseCatalogueCrosswalk:
    citizen_house_design_id: str
    citizen_house_design_code: str
    legacy_place_registry_reference: str
    governed_place_dataset_id: str
    current_place_source: str
    source_catalogue: str
    source_catalogue_sha256: str
    crosswalk_status: str

    def __post_init__(self) -> None:
        if not self.citizen_house_design_id or not self.citizen_house_design_code:
            raise ValueError("house design identity and code required")
        if self.governed_place_dataset_id != "dataset:novegeo:places:v001:700":
            raise ValueError("house crosswalk must reference governed 700-place dataset")
        if self.current_place_source != "settlement_name_catalogue.csv":
            raise ValueError("house crosswalk current source must be settlement_name_catalogue.csv")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_catalogue_sha256):
            raise ValueError("house catalogue sha256 invalid")
        if self.crosswalk_status != "MATCHED_GOVERNED_PLACE_REGISTRY_LINEAGE":
            raise ValueError("house catalogue lineage must remain explicit")


@dataclass(frozen=True, slots=True)
class HouseDesignSiteRequirement:
    citizen_house_design_id: str
    citizen_house_design_code: str
    primary_compatible_terrain_zone: str
    compatible_terrain_zones: tuple[str, ...]
    minimum_plot_area_sqm: Decimal
    suitable_ground_conditions: tuple[str, ...]
    unsuitable_ground_conditions: tuple[str, ...]
    maximum_site_slope_percent: Decimal
    minimum_floor_clearance_mm: int
    flood_resilience_level: str
    wind_resistance_level: str
    drainage_requirement: str
    site_inspection_requirement: str
    physical_property_id_issue_stage: str
    source_catalogue_sha256: str

    def __post_init__(self) -> None:
        if self.minimum_plot_area_sqm <= 0:
            raise ValueError("minimum plot area must be positive")
        if self.maximum_site_slope_percent < 0:
            raise ValueError("maximum site slope cannot be negative")
        if self.minimum_floor_clearance_mm < 0:
            raise ValueError("floor clearance cannot be negative")
        if self.primary_compatible_terrain_zone not in self.compatible_terrain_zones:
            raise ValueError("primary terrain must be included in compatible terrain zones")
        if self.physical_property_id_issue_stage != "validated_construction_commencement":
            raise ValueError("house property identity issuance stage must preserve source contract")


@dataclass(frozen=True, slots=True)
class AddressableSiteCandidate:
    site_id: str
    place_id: str
    administrative_area_id: str
    parcel_id: str
    geometry_id: str
    road_id: str
    road_segment_id: str
    lifecycle_stage: SiteLifecycleStage | str
    runtime_mode: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.site_id.startswith("site:nngla:"):
            raise ValueError("site uses stable opaque site:nngla identity")
        if self.place_id and _PLACE_RE.fullmatch(self.place_id) is None:
            raise ValueError("site place identity invalid")
        if self.administrative_area_id and _ADMIN_RE.fullmatch(self.administrative_area_id) is None:
            raise ValueError("site administrative identity invalid")
        if self.parcel_id and _PARCEL_RE.fullmatch(self.parcel_id) is None:
            raise ValueError("site parcel identity invalid")
        if self.geometry_id and _GEO_RE.fullmatch(self.geometry_id) is None:
            raise ValueError("site geometry identity invalid")
        if self.road_id and _ROAD_RE.fullmatch(self.road_id) is None:
            raise ValueError("site road identity invalid")
        if self.road_segment_id and not self.road_segment_id.startswith("roadseg:nngla:"):
            raise ValueError("site road segment identity invalid")
        stage = self.lifecycle_stage if isinstance(self.lifecycle_stage, SiteLifecycleStage) else SiteLifecycleStage(str(self.lifecycle_stage))
        object.__setattr__(self, "lifecycle_stage", stage)
        if self.runtime_mode not in {"simulation", "production"}:
            raise ValueError("site runtime must be simulation or production")
        if not self.source_reference:
            raise ValueError("site candidate source reference required")


@dataclass(frozen=True, slots=True)
class StructureSiteReference:
    structure_site_reference_id: str
    site_id: str
    structure_reference_type_code: str
    external_registry_code: str
    external_structure_reference: str
    effective_from: str
    effective_to: str
    reference_status: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.structure_site_reference_id.startswith("structsite:nngla:"):
            raise ValueError("structure-site relationship identity invalid")
        if not self.site_id.startswith("site:nngla:"):
            raise ValueError("structure-site relationship site invalid")
        if not self.external_registry_code or not self.external_structure_reference:
            raise ValueError("external structure ownership reference required")
        if self.reference_status not in {"PROPOSED", "ACTIVE", "RETIRED"}:
            raise ValueError("unsupported structure-site reference status")


@dataclass(frozen=True, slots=True)
class SiteAddressAssignmentCandidate:
    assignment_candidate_id: str
    site_id: str
    address_reservation_id: str
    address_id: str
    assignment_status: str
    runtime_mode: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.assignment_candidate_id.startswith("siteaddr:nngla:"):
            raise ValueError("site-address assignment candidate identity invalid")
        if not self.site_id.startswith("site:nngla:"):
            raise ValueError("site-address site identity invalid")
        if not self.address_reservation_id.startswith("addrres:nngla:"):
            raise ValueError("site-address reservation identity invalid")
        if _ADDRESS_RE.fullmatch(self.address_id) is None:
            raise ValueError("site-address must reference governed address identity")
        if self.assignment_status not in {"CANDIDATE", "QUALIFIED", "ASSIGNED"}:
            raise ValueError("unsupported site-address assignment status")
        if self.runtime_mode not in {"simulation", "production"}:
            raise ValueError("site-address runtime invalid")


__all__ = [
    "AddressAllocationPolicy", "SiteLifecycleStage", "RoadSegmentCandidate", "RoadFrontageCandidate",
    "AddressAllocationPolicyDefinition", "AddressSeriesDefinition", "AddressNumberReservation",
    "HouseCatalogueCrosswalk", "HouseDesignSiteRequirement", "AddressableSiteCandidate",
    "StructureSiteReference", "SiteAddressAssignmentCandidate",
]
