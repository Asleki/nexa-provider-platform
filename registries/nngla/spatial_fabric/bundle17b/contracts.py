"""P006.7.11.7 Bundle 17B additive coordinate/environment qualification contracts.

Bundle 17B is read/qualification only.  It consumes the immutable Bundle 17A
spatial source fabric and does not alter existing canonical PostgreSQL rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import re


class EnvironmentEvidenceType(str, Enum):
    DIRECT_SOURCE_OBSERVATION = "DIRECT_SOURCE_OBSERVATION"
    GOVERNED_DERIVATION = "GOVERNED_DERIVATION"
    GOVERNED_INTERPOLATION = "GOVERNED_INTERPOLATION"
    NEAREST_QUALIFIED_OBSERVATION = "NEAREST_QUALIFIED_OBSERVATION"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class SovereignLandRelation(str, Enum):
    INSIDE_SOVEREIGN_LAND = "INSIDE_SOVEREIGN_LAND"
    ON_SOVEREIGN_BOUNDARY = "ON_SOVEREIGN_BOUNDARY"
    OUTSIDE_LAND_EXPECTED_MARINE_CANDIDATE = "OUTSIDE_LAND_EXPECTED_MARINE_CANDIDATE"
    OUTSIDE_LAND_UNEXPECTED = "OUTSIDE_LAND_UNEXPECTED"
    OUTSIDE_GOVERNED_MAP_EXTENT = "OUTSIDE_GOVERNED_MAP_EXTENT"


@dataclass(frozen=True, slots=True)
class CrsCrosswalkEntry:
    crs_crosswalk_id: str
    source_file_id: str
    source_dataset_id: str
    source_crs_form: str
    source_authority_name: str
    source_authority_code: str
    source_coordinate_reference_id: str
    governed_crs_code: str
    axis_order: str
    horizontal_unit: str
    reconciliation_basis: str
    evidence_reference: str
    qualification_status: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-CRSXW-\d{6}", self.crs_crosswalk_id) is None:
            raise ValueError("invalid CRS crosswalk identity")
        if re.fullmatch(r"NG-SPFILE-\d{3}", self.source_file_id) is None:
            raise ValueError("invalid source_file_id")
        if self.governed_crs_code != "NG-CRS-EPSG4326":
            raise ValueError("Bundle 17B must reconcile to the locked NoveGeo WGS84 CRS")
        if self.axis_order != "LONGITUDE_LATITUDE":
            raise ValueError("Bundle 17B axis order must remain LONGITUDE_LATITUDE")
        if self.horizontal_unit != "decimal_degree":
            raise ValueError("Bundle 17B horizontal unit must remain decimal_degree")
        if self.qualification_status != "PASS":
            raise ValueError("persisted CRS crosswalk entries are qualified evidence")


@dataclass(frozen=True, slots=True)
class PrecisionQualification:
    precision_qualification_id: str
    coordinate_occurrence_id: str
    coordinate_candidate_id: str
    axis: str
    source_value: str
    canonical_value: str
    display_value: str
    source_decimal_places: int
    canonical_decimal_places: int
    display_decimal_places: int
    round_trip_same_location: bool
    display_is_authoritative: bool
    precision_status: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-PREC-\d{8}", self.precision_qualification_id) is None:
            raise ValueError("invalid precision qualification identity")
        if self.axis not in {"LONGITUDE", "LATITUDE"}:
            raise ValueError("axis must be LONGITUDE or LATITUDE")
        if self.display_is_authoritative:
            raise ValueError("human display precision can never be authoritative")
        if not self.round_trip_same_location or self.precision_status != "PASS":
            raise ValueError("persisted precision qualification must preserve location")


@dataclass(frozen=True, slots=True)
class ContainmentQualification:
    containment_qualification_id: str
    coordinate_candidate_id: str
    canonical_longitude: Decimal
    canonical_latitude: Decimal
    boundary_id: str
    boundary_version: int
    map_extent_status: str
    sovereign_land_relation: SovereignLandRelation
    sovereign_part_id: str
    boundary_relation: str
    expected_spatial_context: str
    qualification_status: str
    qualification_basis: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-CONT-\d{7}", self.containment_qualification_id) is None:
            raise ValueError("invalid containment qualification identity")
        if self.boundary_id != "boundary:novegeo:sovereign" or self.boundary_version != 2:
            raise ValueError("Bundle 17B must use the locked sovereign boundary v2")
        if self.map_extent_status not in {"WITHIN_GOVERNED_EXTENT", "OUTSIDE_GOVERNED_EXTENT"}:
            raise ValueError("invalid map extent status")
        if self.qualification_status not in {"PASS", "FAIL"}:
            raise ValueError("qualification_status must be PASS or FAIL")


@dataclass(frozen=True, slots=True)
class SourceFidelityResult:
    source_fidelity_result_id: str
    coordinate_occurrence_id: str
    source_file_id: str
    source_record_id: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    expected_source_sha256: str
    actual_source_sha256: str
    source_coordinate_match: str
    source_attribute_match: str
    dataset_lineage_match: str
    crs_lineage_match: str
    fidelity_status: str
    findings: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-FID-\d{8}", self.source_fidelity_result_id) is None:
            raise ValueError("invalid source fidelity result identity")
        if self.fidelity_status not in {"PASS", "FAIL"}:
            raise ValueError("fidelity_status must be PASS or FAIL")


@dataclass(frozen=True, slots=True)
class EnvironmentBinding:
    environment_binding_id: str
    spatial_point_id: str
    spatial_cell_id: str
    coordinate_candidate_id: str
    major_grid_id: str
    sovereign_part_id: str
    elevation_observation_id: str
    elevation_m: str
    elevation_evidence_type: EnvironmentEvidenceType
    terrain_class: str
    terrain_evidence_type: EnvironmentEvidenceType
    climate_observation_id: str
    climate_resolution_distance_degrees: str
    annual_rainfall_mm: str
    mean_temperature_c: str
    mean_wind_speed_mps: str
    prevailing_wind_direction_deg: str
    climate_class: str
    climate_evidence_type: EnvironmentEvidenceType
    vegetation_observation_id: str
    vegetation_resolution_distance_degrees: str
    vegetation_class: str
    aridity_class: str
    vegetation_evidence_type: EnvironmentEvidenceType
    hydrology_reference_id: str
    hydrology_evidence_type: EnvironmentEvidenceType
    environment_resolution_status: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-ENV-BIND-\d{6}", self.environment_binding_id) is None:
            raise ValueError("invalid environment binding identity")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("baseline spatial environment bindings are shared reference")
        if self.environment_resolution_status not in {"PASS", "FAIL"}:
            raise ValueError("environment_resolution_status must be PASS or FAIL")


__all__ = [
    "EnvironmentEvidenceType",
    "SovereignLandRelation",
    "CrsCrosswalkEntry",
    "PrecisionQualification",
    "ContainmentQualification",
    "SourceFidelityResult",
    "EnvironmentBinding",
]
