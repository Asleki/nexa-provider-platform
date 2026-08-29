"""P006.7.11.15.8 governed CITY realization contracts.

The contracts are intentionally CITY-specific and additive.  They bind legacy
coordinate evidence to the already-locked P006.7.11.15.7 CITY authority without
reusing historical Delivery 1-3 CITY adoption tables.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


PLAN_ID = "p006.7.11.15.8-governed-city-realization"
PLAN_VERSION = 1
REALIZATION_VERSION = 1
CRS_CODE = "NG-CRS-EPSG4326"
RUNTIME_EFFECT_SCOPE = "SHARED_REFERENCE"

OFFICIAL_NOVEGEO_CITY_IDS = (
    "NG-ADM-000009",
    "NG-ADM-000032",
    "NG-ADM-000055",
    "NG-ADM-000078",
    "NG-ADM-000101",
    "NG-ADM-000124",
    "NG-ADM-000147",
    "NG-ADM-000170",
)
OFFICIAL_CITY_SET = frozenset(OFFICIAL_NOVEGEO_CITY_IDS)


class RealizationMethod(str, Enum):
    SOURCE_REUSE = "SOURCE_REUSE"
    PARENT_CONTAINED_NORMALIZATION = "PARENT_CONTAINED_NORMALIZATION"


class PlannedAction(str, Enum):
    INSERT_AND_PUBLISH = "INSERT_AND_PUBLISH"
    PUBLISH_EXISTING = "PUBLISH_EXISTING"
    REUSE = "REUSE"


@dataclass(frozen=True, slots=True)
class CitySourceEvidence:
    administrative_area_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    boundary_candidate_id: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    source_dataset_sha256: str
    source_geometry_sha256: str
    geometry_type_code: str
    geometry: dict[str, Any]


@dataclass(frozen=True, slots=True)
class CityIdentity:
    administrative_area_id: str
    canonical_name: str
    region_code: str


@dataclass(frozen=True, slots=True)
class ParentRegionAuthority:
    region_id: str
    canonical_name: str
    region_code: str
    region_geometry_id: str
    geometry_sha256: str


@dataclass(frozen=True, slots=True)
class RealizedGeometry:
    method: RealizationMethod
    geometry_type_code: str
    geometry: dict[str, Any]
    geometry_sha256: str
    label_point: dict[str, Any]
    source_area_m2: float
    source_outside_parent_m2: float
    source_outside_parent_ratio: float
    final_area_m2: float
    final_area_km2: float
    final_perimeter_m: float
    final_perimeter_km: float
    area_removed_m2: float
    area_removed_ratio: float


@dataclass(frozen=True, slots=True)
class CurrentCityAuthority:
    city_geometry_id: str
    geometry_sha256: str
    parent_region_id: str
    parent_region_geometry_id: str
    parent_region_geometry_sha256: str
    realization_method: str
    realization_version: int
    effective_from: str
    publication_id: str | None
    publication_status: str | None


@dataclass(frozen=True, slots=True)
class CityRealizationPlan:
    database_name: str
    environment_name: str
    repository_revision: str
    effective_date: str
    city_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    boundary_candidate_id: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    source_dataset_sha256: str
    source_geometry_sha256: str
    parent_region_id: str
    parent_region_name: str
    parent_region_geometry_id: str
    parent_region_geometry_sha256: str
    realization_method: str
    realization_version: int
    city_geometry_id: str
    publication_id: str
    planned_action: str
    geometry_type_code: str
    crs_code: str
    geometry: dict[str, Any]
    geometry_sha256: str
    label_point: dict[str, Any]
    source_area_m2: float
    source_outside_parent_m2: float
    source_outside_parent_ratio: float
    area_m2: float
    area_km2: float
    perimeter_m: float
    perimeter_km: float
    area_removed_m2: float
    area_removed_ratio: float
    fingerprint: str

    @property
    def confirmation_token(self) -> str:
        return f"REALIZE-NNGLA-CITY::{self.database_name}::{self.fingerprint}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["planId"] = PLAN_ID
        payload["planVersion"] = PLAN_VERSION
        payload["confirmationToken"] = self.confirmation_token
        return payload


@dataclass(frozen=True, slots=True)
class CityExecutionResult:
    execution_id: str
    fingerprint: str
    city_id: str
    city_geometry_id: str
    publication_id: str
    database_name: str
    environment_name: str
    repository_revision: str
    status: str
    replayed: bool
    inserted_geometry_count: int
    reused_geometry_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
