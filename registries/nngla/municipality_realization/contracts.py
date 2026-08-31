"""P006.7.11.15.9.1 governed MUNICIPALITY realization contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

PLAN_ID = "p006.7.11.15.9.1-governed-municipality-realization"
PLAN_VERSION = 1
REALIZATION_VERSION = 1
CRS_CODE = "NG-CRS-EPSG4326"
RUNTIME_EFFECT_SCOPE = "SHARED_REFERENCE"
EXPECTED_MUNICIPALITY_COUNT = 24
EXPECTED_PER_REGION = 3


class RealizationMethod(str, Enum):
    SOURCE_REUSE = "SOURCE_REUSE"
    REGION_CITY_CONTAINED_NORMALIZATION = "REGION_CITY_CONTAINED_NORMALIZATION"


@dataclass(frozen=True, slots=True)
class MunicipalitySourceEvidence:
    administrative_area_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    parent_source_record_id: str
    boundary_candidate_id: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    source_dataset_sha256: str
    source_geometry_sha256: str
    geometry_type_code: str
    geometry: dict[str, Any]


@dataclass(frozen=True, slots=True)
class MunicipalityIdentity:
    administrative_area_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    parent_source_record_id: str


@dataclass(frozen=True, slots=True)
class ParentRegionAuthority:
    region_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    region_geometry_id: str
    geometry_sha256: str


@dataclass(frozen=True, slots=True)
class ParentCityAuthority:
    city_id: str
    city_geometry_id: str
    geometry_sha256: str
    publication_id: str


@dataclass(frozen=True, slots=True)
class RealizedMunicipality:
    municipality_id: str
    realization_method: str
    geometry_type_code: str
    geometry: dict[str, Any]
    geometry_sha256: str
    label_point: dict[str, Any]
    source_area_m2: float
    source_outside_region_m2: float
    source_city_overlap_m2: float
    area_m2: float
    area_km2: float
    perimeter_m: float
    perimeter_km: float


@dataclass(frozen=True, slots=True)
class PartitionEvidence:
    all_valid: bool
    all_non_empty: bool
    all_polygonal: bool
    all_covered_by_region: bool
    city_covered_by_region: bool
    municipality_sibling_positive_overlap_m2: float
    city_municipality_positive_overlap_m2: float
    union_equals_region: bool
    union_area_m2: float
    region_area_m2: float
    symmetric_difference_m2: float
    partition_status: str


@dataclass(frozen=True, slots=True)
class MunicipalityRegionPlan:
    database_name: str
    environment_name: str
    repository_revision: str
    effective_date: str
    parent_region_id: str
    parent_region_name: str
    region_code: str
    parent_region_geometry_id: str
    parent_region_geometry_sha256: str
    city_id: str
    city_geometry_id: str
    city_geometry_sha256: str
    city_publication_id: str
    partition_qualification_id: str
    municipality_geometry_set_sha256: str
    municipality_member_set: tuple[dict[str, str], ...]
    municipalities: tuple[dict[str, Any], ...]
    partition: dict[str, Any]
    fingerprint: str

    @property
    def confirmation_token(self) -> str:
        return f"REALIZE-NNGLA-MUNICIPALITY::{self.database_name}::{self.fingerprint}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["planId"] = PLAN_ID
        payload["planVersion"] = PLAN_VERSION
        payload["confirmationToken"] = self.confirmation_token
        return payload


@dataclass(frozen=True, slots=True)
class MunicipalityExecutionResult:
    execution_id: str
    fingerprint: str
    parent_region_id: str
    database_name: str
    environment_name: str
    repository_revision: str
    status: str
    replayed: bool
    inserted_count: int
    reused_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
